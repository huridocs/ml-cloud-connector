import logging
import tempfile
import time
import inspect
import requests
from google.api_core.exceptions import GoogleAPICallError, BadRequest
from googleapiclient import discovery
from googleapiclient.errors import HttpError
from httpx import ConnectTimeout, HTTPStatusError, ReadTimeout, RemoteProtocolError
from pathlib import Path
from typing import Callable
from google.cloud import compute_v1

from ml_cloud_connector.configuration import PROJECT_ID, ZONE, INSTANCE_ID


class MlCloudConnector:
    IP_CACHE_PATH = Path(tempfile.gettempdir(), f"{INSTANCE_ID}.txt")

    def __init__(self):
        self.client = None
        if PROJECT_ID and ZONE and INSTANCE_ID:
            # You should loging first with gcloud auth application-default login
            self.client = compute_v1.InstancesClient()
            self.project = PROJECT_ID
            self.zone = ZONE
            self.instance = INSTANCE_ID

    def is_active(self):
        instance_info = self.client.get(project=self.project, zone=self.zone, instance=self.instance)
        if instance_info.status == "RUNNING":
            print("Instance is active")
            return True
        return False

    def start(self):
        if self.is_active():
            return True

        self.client.start(project=self.project, zone=self.zone, instance=self.instance)

        for i in range(100):
            if self.is_active():
                return True
            time.sleep(5)
            self.client.start(project=self.project, zone=self.zone, instance=self.instance)
        return False

    def stop(self):
        if not self.is_active():
            print("Already stopped")
            return True

        self.client.stop(project=self.project, zone=self.zone, instance=self.instance)

        for i in range(100):
            if not self.is_active():
                print("stopped")
                return True
            time.sleep(5)
            self.client.stop(project=self.project, zone=self.zone, instance=self.instance)
        return False

    def restart(self):
        if not self.stop():
            return False
        return self.start()

    def get_ip(self, port: int = 0):
        if not self.client:
            return "localhost"

        service_running = requests.get(f"http://localhost:{port}", timeout=3).status_code == 200 if port else False

        if self.IP_CACHE_PATH.exists() and service_running:
            return self.IP_CACHE_PATH.read_text()

        if self.IP_CACHE_PATH.exists() and self.is_active():
            return self.IP_CACHE_PATH.read_text()

        while not self.start():
            self.switch_to_new_instance()
            time.sleep(300)

        # if not self.start():
        #     raise BrokenPipeError("MlCloudConnector failed to start the instance from get ip method")

        instance_info = self.client.get(project=self.project, zone=self.zone, instance=self.instance)
        return instance_info.network_interfaces[0].access_configs[0].nat_i_p

    def execute(self, function: Callable, service_logger: logging.Logger, *args, **kwargs):
        signature = inspect.signature(function)
        connection_wait_time = 180
        reconnect_trial_count = 0
        request_trial_count = 0
        while reconnect_trial_count < 10:
            try:
                bound_args = signature.bind(*args, **kwargs)
                bound_args.apply_defaults()
                return_value = function(*bound_args.args, **bound_args.kwargs)
                return return_value, True, ""
            except ReadTimeout:
                if request_trial_count == 5:
                    return "There is a problem with getting the response.", False
                service_logger.warning(f"Response timeout. Retrying... [Trial: {request_trial_count + 1}]")
                request_trial_count += 1

            except (ConnectTimeout, HTTPStatusError, RemoteProtocolError, KeyError):
                service_logger.error(f"Connection timeout. Retrying... [Trial: {reconnect_trial_count + 1}]")
                self.stop()
                time.sleep(connection_wait_time)
                connection_wait_time *= 1.5
                if connection_wait_time > 900:
                    connection_wait_time = 900
                self.start()
                time.sleep(30)
                reconnect_trial_count += 1
            except Exception as e:
                raise Exception(f"Error in executing the function: {str(e)}")
        return None, False, "Response not returned. Server error."



    def is_gpu_available(self):
        instance_info = self.client.get(project=self.project, zone=self.zone, instance=self.instance)
        return True if instance_info.guest_accelerators else False


    def wait_for_operation(self, compute, operation):
        print('Waiting for operation to finish...')
        operation_name = operation['name']

        if 'zone' in operation:
            operation_scope = 'zone'
            scope_name = operation['zone'].split('/')[-1]
        elif 'region' in operation:
            operation_scope = 'region'
            scope_name = operation['region'].split('/')[-1]
        else:
            operation_scope = 'global'
            scope_name = None

        while True:
            if operation_scope == 'zone':
                result = compute.zoneOperations().get(
                    project=self.project,
                    zone=scope_name,
                    operation=operation_name).execute()
            elif operation_scope == 'region':
                result = compute.regionOperations().get(
                    project=self.project,
                    region=scope_name,
                    operation=operation_name).execute()
            else:
                result = compute.globalOperations().get(
                    project=self.project,
                    operation=operation_name).execute()

            if 'error' in result:
                if result['error']['errors'][0]['code'] == 'ZONE_RESOURCE_POOL_EXHAUSTED_WITH_DETAILS':
                    raise GoogleAPICallError(result['error'])
                raise Exception(result['error'])

            if result['status'] == 'DONE':
                print("Operation completed.")
                if 'error' in result:
                    print("Error in operation:", result['error'])
                break
            time.sleep(5)

    def snapshot_exists(self, compute, snapshot_name):
        try:
            snapshot = compute.snapshots().get(project=self.project, snapshot=snapshot_name).execute()
            if snapshot:
                print(f"Snapshot '{snapshot_name}' already exists.")
                return True
        except HttpError as e:
            if e.resp.status == 404:
                print(f"Snapshot '{snapshot_name}' does not exist. Will create it.")
                return False
            else:
                print(f"Error checking snapshot existence: {e}")
                raise
        return False


    def disk_exists(self, compute, zone, disk_name):
        try:
            disk = compute.disks().get(project=self.project, zone=zone, disk=disk_name).execute()
            if disk:
                print(f"Disk '{disk_name}' already exists in zone '{zone}'.")
                return True
        except HttpError as e:
            if e.resp.status == 404:
                print(f"Disk '{disk_name}' does not exist in zone '{zone}'. Will create it.")
                return False
            else:
                print(f"Error checking disk existence: {e}")
                raise
        return False


    def get_zones_with_accelerator(self, compute, accelerator_type, machine_type):
        zones_with_accelerator = []
        zones_request = compute.zones().list(project=self.project)

        while zones_request is not None:
            response = zones_request.execute()
            for zone in response.get('items', []):
                zone_name = zone['name']
                try:
                    accelerator_types = compute.acceleratorTypes().list(project=self.project, zone=zone_name).execute()
                    has_accelerator = any(acc['name'] == accelerator_type for acc in accelerator_types.get('items', []))

                    machine_types = compute.machineTypes().list(project=self.project, zone=zone_name).execute()
                    has_machine_type = any(mt['name'] == machine_type for mt in machine_types.get('items', []))

                    if has_accelerator and has_machine_type:
                        print(f"Zone '{zone_name}' supports both '{accelerator_type}' and '{machine_type}'.")
                        zones_with_accelerator.append(zone_name)

                    else:
                        if not has_accelerator:
                            print(f"Zone '{zone_name}' does NOT support accelerator '{accelerator_type}'.")
                        if not has_machine_type:
                            print(f"Zone '{zone_name}' does NOT support machine type '{machine_type}'.")

                except HttpError as e:
                    print(f"Error checking accelerators in zone {zone_name}: {e}")
            zones_request = compute.zones().list_next(previous_request=zones_request, previous_response=response)

        return zones_with_accelerator


    def create_instance(self, compute, target_zone, new_disk_name, instance, new_instance_name, accelerator_type,
                        machine_type, accelerator_count=1):

        print(f'Creating new instance: {new_instance_name} in zone {target_zone}')
        machine_type_full = f'projects/{self.project}/zones/{target_zone}/machineTypes/{machine_type}'
        network_interface = instance['networkInterfaces'][0]
        config = {
            'name': new_instance_name,
            'machineType': machine_type_full,
            'disks': [
                {
                    'boot': True,
                    'autoDelete': True,
                    'source': f'projects/{self.project}/zones/{target_zone}/disks/{new_disk_name}',
                    'deviceName': new_disk_name,
                }
            ],
            'networkInterfaces': [
                {
                    'network': network_interface['network'],
                    'subnetwork': network_interface.get('subnetwork'),
                    'accessConfigs': [
                        {
                            'type': 'ONE_TO_ONE_NAT',
                            'name': 'External NAT'
                        }
                    ]
                }
            ],
            'tags': instance.get('tags', {}),
            'metadata': instance.get('metadata', {}),
            'serviceAccounts': instance.get('serviceAccounts', []),
            'scheduling': instance.get('scheduling', {}),
            'labels': instance.get('labels', {}),
        }

        if accelerator_type and accelerator_count > 0:
            config['guestAccelerators'] = [
                {
                    'acceleratorType': f'projects/{self.project}/zones/{target_zone}/acceleratorTypes/{accelerator_type}',
                    'acceleratorCount': accelerator_count
                }
            ]

        max_retries = 3
        delay = 60

        for attempt in range(max_retries):
            try:
                operation = compute.instances().insert(
                    project=self.project,
                    zone=target_zone,
                    body=config
                ).execute()
                self.wait_for_operation(compute, operation)

            except GoogleAPICallError as e:
                # if "ZONE_RESOURCE_POOL_EXHAUSTED_WITH_DETAILS" in str(e):
                if attempt < max_retries - 1:
                    print(f"Resources not available. Retrying in {delay} seconds... [Trial: {attempt + 1}]")
                    time.sleep(delay)
                else:
                    print(f"Max retries [{max_retries}] reached. Trying other zones...")
                    raise


        # operation = compute.instances().insert(
        #     project=self.project,
        #     zone=target_zone,
        #     body=config
        # ).execute()
        # self.wait_for_operation(compute, operation)

        new_instance = compute.instances().get(
            project=self.project,
            zone=target_zone,
            instance=new_instance_name
        ).execute()
        return new_instance


    def create_snapshot(self, compute, boot_disk, snapshot_name):
        print(f'Creating snapshot: {snapshot_name}')
        snapshot_body = {
            'name': snapshot_name,
        }
        operation = compute.disks().createSnapshot(
            project=self.project,
            zone=self.zone,
            disk=boot_disk,
            body=snapshot_body
        ).execute()
        self.wait_for_operation(compute, operation)


    def create_disk(self, compute, target_zone, new_disk_name, snapshot_name):
        print(f'Creating new disk: {new_disk_name} in zone {target_zone} from snapshot {snapshot_name}')
        disk_body = {
            'name': new_disk_name,
            'sourceSnapshot': f'projects/{self.project}/global/snapshots/{snapshot_name}',
            'type': f'projects/{self.project}/zones/{target_zone}/diskTypes/pd-standard'
        }

        operation = compute.disks().insert(
            project=self.project,
            zone=target_zone,
            body=disk_body
        ).execute()
        self.wait_for_operation(compute, operation)

    def delete_disk(self, zone, disk_name):
        print(f"Deleting disk: {disk_name} in zone {zone}")
        try:
            time.sleep(10)
            disks_client = compute_v1.DisksClient()
            operation = disks_client.delete(project=self.project, zone=zone, disk=disk_name)
            operation.result()
        except BadRequest as e:
            print(f"Disk deletion [{disk_name}] failed: {e}")

    def switch_to_new_instance(self):

        compute = discovery.build('compute', 'v1')
        machine_type = "g2-standard-4"
        accelerator_type = "nvidia-l4"
        available_zones = self.get_zones_with_accelerator(compute, accelerator_type, machine_type)
        target_zones = [zone for zone in available_zones if zone.startswith("europe-west4")]
        snapshot_name = f'snapshot-{self.instance}'
        new_instance_name = f'snapshot-{self.instance}-instance'
        new_disk_name = f'snapshot-{self.instance}-disk'
        print(f"AVAILABLE ZONES: {available_zones}")
        print(f"TARGET ZONES: {target_zones}")

        for target_zone in target_zones:
            self.stop()
            print(f"\nAttempting to create instance in zone: {target_zone}")

            try:
                instance = compute.instances().get(
                    project=self.project,
                    zone=self.zone,
                    instance=self.instance
                ).execute()

                boot_disk = None
                for disk in instance['disks']:
                    if disk.get('boot'):
                        boot_disk = disk['source'].split('/')[-1]
                        break
                if not boot_disk:
                    raise Exception("Boot disk not found.")

                if not self.snapshot_exists(compute, snapshot_name):
                    self.create_snapshot(compute, boot_disk, snapshot_name)
                else:
                    print(f"Using existing snapshot: {snapshot_name}")

                if not self.disk_exists(compute, target_zone, new_disk_name):
                    self.create_disk(compute, target_zone, new_disk_name, snapshot_name)
                else:
                    print(f"Using existing disk: {new_disk_name}")

                try:
                    new_instance = self.create_instance(compute, target_zone, new_disk_name, instance, new_instance_name, accelerator_type, machine_type)
                except GoogleAPICallError as e:
                    self.delete_disk(target_zone, new_disk_name)
                    if target_zone == target_zones[-1]:
                        raise Exception("Instance creation failed on all available zones.")
                    else:
                        continue

                print(f'Instance snapshot-{self.instance}-instance created in zone {target_zone}.')
                self.instance = new_instance['id']
                self.zone = target_zone
                break

            except HttpError as err:
                print(f"An error occurred while creating the instance on {target_zone}: {err}")
                if target_zone == target_zones[-1]:
                    # raise Exception("Instance creation failed on all available zones.")
                    print("Instance creation failed on all available zones.")
                else:
                    continue



if __name__ == '__main__':
    connector = MlCloudConnector()
    print(connector.is_gpu_available())

    # connector.create_new_instance()
    # connector.get_zones_with_accelerator(accelerator_type)
    # print(connector.client.get(project=connector.project, zone=connector.zone, instance=connector.instance))
    # connector.switch_to_new_instance()
    # print(connector.client.get(project=connector.project, zone=connector.zone, instance=connector.instance).disks[0])


    # compute = discovery.build('compute', 'v1')
    # instance = compute.instances().get(
    #     project=connector.project,
    #     zone=connector.zone,
    #     instance=connector.instance
    # ).execute()
    #
    # print(instance)


    # compute = discovery.build('compute', 'v1')
    # target_zone = "europe-west4-a"
    # instance = compute.instances().get(
    #     project=connector.project,
    #     zone=connector.zone,
    #     instance=connector.instance
    # ).execute()
    # print(instance)
    # print("*"*20)
    # print(instance['machineType'].split('/')[-1])
