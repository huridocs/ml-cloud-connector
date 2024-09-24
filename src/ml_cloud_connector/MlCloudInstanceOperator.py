import time
from datetime import datetime
from google.api_core.exceptions import GoogleAPICallError
from googleapiclient.errors import HttpError
from ml_cloud_connector.MlCloudDiskOperator import MlCloudDiskOperator
from ml_cloud_connector.wait_for_operation import wait_for_operation


class MlCloudInstanceOperator:
    def __init__(self, project, service_logger, server_type: str):
        self.project = project
        self.service_logger = service_logger
        self.server_type = server_type

    def create_instance(
        self,
        compute,
        target_zone,
        new_disk_name,
        new_instance_name="",
        accelerator_type="nvidia-l4",
        machine_type="g2-standard-4",
        accelerator_count=1,
    ):
        if not new_instance_name:
            current_time = datetime.now().strftime("%Y%m%d-%H%M%S")
            new_instance_name = f"instance-{current_time}"

        self.service_logger.info(f"Creating new instance: {new_instance_name} in zone {target_zone}")
        machine_type_full = f"projects/{self.project}/zones/{target_zone}/machineTypes/{machine_type}"
        config = {
            "name": new_instance_name,
            "machineType": machine_type_full,
            "disks": [
                {
                    "boot": True,
                    "autoDelete": True,
                    "source": f"projects/{self.project}/zones/{target_zone}/disks/{new_disk_name}",
                    "deviceName": new_disk_name,
                }
            ],
            "networkInterfaces": [
                {
                    "network": "https://www.googleapis.com/compute/v1/projects/publaynet/global/networks/default",
                    "subnetwork": "https://www.googleapis.com/compute/v1/projects/publaynet/regions/europe-west4/subnetworks/default",
                    "accessConfigs": [{"type": "ONE_TO_ONE_NAT", "name": "External NAT"}],
                }
            ],
            "tags": {"items": ["http-server", "https-server", "ollama-server"], "fingerprint": "n79AIbZ_p0c="},
            "metadata": {"kind": "compute#metadata", "fingerprint": "UN94vBlYHOE="},
            "serviceAccounts": [
                {
                    "email": "610489196507-compute@developer.gserviceaccount.com",
                    "scopes": [
                        "https://www.googleapis.com/auth/devstorage.read_only",
                        "https://www.googleapis.com/auth/logging.write",
                        "https://www.googleapis.com/auth/monitoring.write",
                        "https://www.googleapis.com/auth/service.management.readonly",
                        "https://www.googleapis.com/auth/servicecontrol",
                        "https://www.googleapis.com/auth/trace.append",
                    ],
                }
            ],
            "scheduling": {
                "onHostMaintenance": "TERMINATE",
                "automaticRestart": True,
                "preemptible": False,
                "provisioningModel": "STANDARD",
            },
            "labels": {},
        }

        if accelerator_type and accelerator_count > 0:
            config["guestAccelerators"] = [
                {
                    "acceleratorType": f"projects/{self.project}/zones/{target_zone}/acceleratorTypes/{accelerator_type}",
                    "acceleratorCount": accelerator_count,
                }
            ]

        max_retries = 3
        delay = 60

        for attempt in range(max_retries):
            try:
                operation = compute.instances().insert(project=self.project, zone=target_zone, body=config).execute()
                wait_for_operation(self.project, compute, operation, self.service_logger)
                break

            except GoogleAPICallError as e:
                if attempt < max_retries - 1:
                    self.service_logger.info(
                        f"Resources not available. Retrying in {delay} seconds... [Trial: {attempt + 1}]"
                    )
                    time.sleep(delay)
                else:
                    self.service_logger.info(f"Max retries [{max_retries}] reached. Trying other zones...")
                    raise

        new_instance = compute.instances().get(project=self.project, zone=target_zone, instance=new_instance_name).execute()
        return new_instance

    @staticmethod
    def get_instance_configuration(compute, project, zone, instance):
        return compute.instances().get(project=project, zone=zone, instance=instance).execute()

    def is_zone_available(self, accelerator_type, compute, machine_type, zone_name):
        accelerator_types = compute.acceleratorTypes().list(project=self.project, zone=zone_name).execute()
        has_accelerator = any(acc["name"] == accelerator_type for acc in accelerator_types.get("items", []))
        machine_types = compute.machineTypes().list(project=self.project, zone=zone_name).execute()
        has_machine_type = any(mt["name"] == machine_type for mt in machine_types.get("items", []))
        return has_accelerator and has_machine_type

    def get_zones_with_accelerator(self, compute, accelerator_type="nvidia-l4", machine_type="g2-standard-4"):
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

    def create_instance_from_snapshot(self, compute):
        snapshot_name = f"{self.server_type}-server-snapshot"
        disk_operator = MlCloudDiskOperator(self.project, self.service_logger)
        available_zones = self.get_zones_with_accelerator(compute)
        target_zones = [zone for zone in available_zones if zone.startswith("europe-west4")]

        for target_zone in target_zones:
            current_time = datetime.now().strftime("%Y%m%d-%H%M%S")
            new_disk_name = f"{self.server_type}-server-disk-" + current_time
            new_instance_name = f"{self.server_type}-server-instance-" + current_time
            self.service_logger.info(f"\nAttempting to create instance in zone: {target_zone}")
            disk_operator.prepare_disk(compute, target_zone, new_disk_name, snapshot_name)
            try:
                new_instance = self.create_instance(compute, target_zone, new_disk_name, new_instance_name)
                self.service_logger.info(f"Instance created in zone {target_zone}.")
                return new_instance["id"], target_zone

            except (GoogleAPICallError, HttpError) as err:
                self.service_logger.info(f"An error occurred while creating the instance on {target_zone}: {err}")
                disk_operator.delete_disk(target_zone, new_disk_name)
                continue

            except Exception as e:
                self.service_logger.info(f"An unexpected error occurred: {e}")
                raise
        return None, None
