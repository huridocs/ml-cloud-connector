import logging
import tempfile
import time
import inspect
import requests
from requests.exceptions import ConnectionError
from google.api_core.exceptions import GoogleAPICallError
from googleapiclient import discovery
from googleapiclient.errors import HttpError
from httpx import ConnectTimeout, HTTPStatusError, ReadTimeout, RemoteProtocolError, ConnectError
from pathlib import Path
from typing import Callable
from google.cloud import compute_v1

from ml_cloud_connector.MlCloudDiskOperator import MlCloudDiskOperator
from ml_cloud_connector.MlCloudInstanceOperator import MlCloudInstanceOperator
from ml_cloud_connector.MlCloudSnapshotOperator import MlCloudSnapshotOperator
from ml_cloud_connector.configuration import PROJECT_ID, ZONE, INSTANCE_ID


class MlCloudConnector:
    IP_CACHE_PATH = Path(tempfile.gettempdir(), f"{INSTANCE_ID}.txt")

    def __init__(self, service_logger=None):
        self.client = None
        if PROJECT_ID and ZONE and INSTANCE_ID:
            # You should loging first with gcloud auth application-default login
            self.client = compute_v1.InstancesClient()
            self.project = PROJECT_ID
            self.zone = ZONE
            self.instance = INSTANCE_ID
        if not service_logger:
            handlers = [logging.StreamHandler()]
            logging.root.handlers = []
            logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s", handlers=handlers)
            service_logger = logging.getLogger()
        self.service_logger = service_logger

    def is_active(self):
        instance_info = self.client.get(project=self.project, zone=self.zone, instance=self.instance)
        if instance_info.status == "RUNNING":
            self.service_logger.info("Instance is active")
            return True
        return False

    def start_attempt_with_instance_switch(self):
        while not self.start():
            switched = self.switch_to_new_instance()
            if switched:
                self.stop()
                time.sleep(120)
            else:
                wait_time = 300
                self.service_logger.info("Switching to new instance failed on all available zones.")
                self.service_logger.info(f"The process will be restarted after {wait_time} seconds.")
                time.sleep(wait_time)

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
            self.service_logger.info("Already stopped")
            return True

        self.client.stop(project=self.project, zone=self.zone, instance=self.instance)

        for i in range(100):
            if not self.is_active():
                self.service_logger.info("stopped")
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

        self.start_attempt_with_instance_switch()
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

            except (ConnectError, ReadTimeout):
                if request_trial_count == 10:
                    return None, False, "There is a problem with getting the response."
                service_logger.warning(f"Response timeout. Retrying... [Trial: {request_trial_count + 1}]")
                request_trial_count += 1

            except (ConnectionError, ConnectTimeout, HTTPStatusError, RemoteProtocolError, KeyError):
                service_logger.error(f"Connection timeout. Retrying... [Trial: {reconnect_trial_count + 1}]")
                self.stop()
                time.sleep(connection_wait_time)
                connection_wait_time *= 1.5
                if connection_wait_time > 900:
                    connection_wait_time = 900
                self.start_attempt_with_instance_switch()
                time.sleep(30)
                reconnect_trial_count += 1
            except Exception as e:
                raise Exception(f"Error in executing the function: {str(e)}")
        return None, False, "Response not returned. Server error."

    def is_gpu_available(self):
        instance_info = self.client.get(project=self.project, zone=self.zone, instance=self.instance)
        return True if instance_info.guest_accelerators else False

    def get_zones_with_accelerator(self, compute, accelerator_type, machine_type):
        zones_with_accelerator = []
        zones_request = compute.zones().list(project=self.project)
        self.service_logger.info(f"\nGetting available zones for '{accelerator_type}' and '{machine_type}'...")

        while zones_request is not None:
            response = zones_request.execute()
            for zone in response.get("items", []):
                zone_name = zone["name"]
                try:
                    zone_available = self.is_zone_available(accelerator_type, compute, machine_type, zone_name)
                    if zone_available:
                        zones_with_accelerator.append(zone_name)
                except HttpError as e:
                    self.service_logger.info(f"Error checking accelerators in zone {zone_name}: {e}")
            zones_request = compute.zones().list_next(previous_request=zones_request, previous_response=response)

        self.service_logger.info(f"Available zones for '{accelerator_type}' and '{machine_type}': {zones_with_accelerator}")

        return zones_with_accelerator

    def is_zone_available(self, accelerator_type, compute, machine_type, zone_name):
        accelerator_types = compute.acceleratorTypes().list(project=self.project, zone=zone_name).execute()
        has_accelerator = any(acc["name"] == accelerator_type for acc in accelerator_types.get("items", []))
        machine_types = compute.machineTypes().list(project=self.project, zone=zone_name).execute()
        has_machine_type = any(mt["name"] == machine_type for mt in machine_types.get("items", []))
        return has_accelerator and has_machine_type

    def switch_to_new_instance(self):

        compute = discovery.build("compute", "v1")
        machine_type = "g2-standard-4"
        accelerator_type = "nvidia-l4"
        snapshot_name = f"snapshot-{self.instance}"
        new_instance_name = f"snapshot-{self.instance}-instance"
        new_disk_name = f"snapshot-{self.instance}-disk"
        disk_operator = MlCloudDiskOperator(self.project, self.service_logger)
        snapshot_operator = MlCloudSnapshotOperator(self.project, self.service_logger)
        instance_operator = MlCloudInstanceOperator(self.project, self.zone, self.instance, self.service_logger)

        available_zones = self.get_zones_with_accelerator(compute, accelerator_type, machine_type)
        target_zones = [zone for zone in available_zones if zone.startswith("europe-west4")]

        self.stop()

        base_instance = instance_operator.get_instance_configuration(compute)
        boot_disk = disk_operator.get_boot_disk(base_instance)
        snapshot_operator.prepare_snapshot(compute, self.zone, snapshot_name, boot_disk)

        for target_zone in target_zones:
            self.service_logger.info(f"\nAttempting to create instance in zone: {target_zone}")
            disk_operator.prepare_disk(compute, target_zone, new_disk_name, snapshot_name)
            try:
                new_instance = instance_operator.create_instance(
                    compute, target_zone, new_disk_name, base_instance, new_instance_name, accelerator_type, machine_type
                )
                self.service_logger.info(f"Instance snapshot-{self.instance}-instance created in zone {target_zone}.")
                self.instance = new_instance["id"]
                self.zone = target_zone
                return True

            except (GoogleAPICallError, HttpError) as err:
                self.service_logger.info(f"An error occurred while creating the instance on {target_zone}: {err}")
                disk_operator.delete_disk(target_zone, new_disk_name)
                continue

            except Exception as e:
                self.service_logger.info(f"An unexpected error occurred: {e}")
                raise
        return False


if __name__ == "__main__":
    connector = MlCloudConnector()
    print(connector.is_gpu_available())
