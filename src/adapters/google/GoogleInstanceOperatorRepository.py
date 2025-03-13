from logging import Logger
from typing import Optional
from google.cloud import compute_v1
from googleapiclient import discovery
from google.api_core.exceptions import GoogleAPICallError
from adapters.google.GoogleCloudConfig import GoogleCloudConfig
from adapters.google.Disk import Disk
from adapters.google.Instance import Instance
from ports.InstanceOperatorRepository import InstanceOperatorRepository


class GoogleInstanceOperatorRepository(InstanceOperatorRepository):
    def __init__(self, project_id: str, logger: Logger):
        self.project_id = project_id
        self.logger = logger
        self.compute_client = compute_v1.InstancesClient()
        self.compute = discovery.build("compute", "v1")

    def start_instance(self, zone: str, instance_id: str) -> bool:
        try:
            operation = self.compute_client.start(project=self.project_id, zone=zone, instance=instance_id)
            operation.result()  # wait for completion
            return True
        except Exception as e:
            self.logger.error(f"Failed to start instance {instance_id}: {str(e)}")
            return False

    def stop_instance(self, zone: str, instance_id: str) -> bool:
        try:
            operation = self.compute_client.stop(project=self.project_id, zone=zone, instance=instance_id)
            operation.result()  # wait for completion
            return True
        except Exception as e:
            self.logger.error(f"Failed to stop instance {instance_id}: {str(e)}")
            return False

    def get_boot_disk(self, zone: str, instance_id: str) -> str:
        try:
            instance = self.get_instance(zone, instance_id)
            if instance and instance.boot_disk:
                return instance.boot_disk
            raise Exception("Boot disk not found")
        except Exception as e:
            self.logger.error(f"Failed to get boot disk for instance {instance_id}: {str(e)}")
            raise

    def create_instance(self, name: str, zone: str, config: GoogleCloudConfig, disk: Disk) -> Optional[Instance]:
        try:
            instance_config = self.build_instance_config(name, zone, config, disk)
            operation = self.compute.instances().insert(project=self.project_id, zone=zone, body=instance_config).execute()
            self.wait_for_operation(operation, zone)
            instance_data = self.compute.instances().get(project=self.project_id, zone=zone, instance=name).execute()
            return self.convert_to_instance_entity(instance_data)

        except GoogleAPICallError as e:
            self.logger.error(f"Failed to create instance: {str(e)}")
            raise

    def get_instance(self, zone: str, instance_id: str) -> Optional[Instance]:
        try:
            instance_data = self.compute.instances().get(project=self.project_id, zone=zone, instance=instance_id).execute()
            return self.convert_to_instance_entity(instance_data)
        except Exception as e:
            self.logger.error(f"Failed to get instance {instance_id}: {str(e)}")
            return None

    def delete_instance(self, zone: str, instance_id: str) -> bool:
        try:
            operation = self.compute_client.delete(project=self.project_id, zone=zone, instance=instance_id)
            operation.result()
            return True
        except Exception as e:
            self.logger.error(f"Failed to delete instance {instance_id}: {str(e)}")
            return False

    def build_instance_config(self, name: str, zone: str, config: GoogleCloudConfig, disk: Disk) -> dict:
        instance_config = {
            "name": name,
            "machineType": f"projects/{self.project_id}/zones/{zone}/machineTypes/{config.default_machine_type}",
            "disks": [
                {
                    "boot": True,
                    "autoDelete": True,
                    "source": f"projects/{self.project_id}/zones/{zone}/disks/{disk.name}",
                    "deviceName": disk.name,
                }
            ],
            "networkInterfaces": config.network_configuration["networkInterfaces"],
            "scheduling": config.network_configuration["scheduling"],
        }

        if config.default_accelerator_type and config.default_accelerator_count > 0:
            instance_config["guestAccelerators"] = [
                {
                    "acceleratorType": f"projects/{self.project_id}/zones/{zone}/acceleratorTypes/{config.default_accelerator_type}",
                    "acceleratorCount": config.default_accelerator_count,
                }
            ]

        return instance_config

    @staticmethod
    def convert_to_instance_entity(instance_data: dict) -> Instance:
        return Instance(
            id=str(instance_data["id"]),
            name=instance_data["name"],
            zone=instance_data["zone"].split("/")[-1],
            machine_type=instance_data["machineType"].split("/")[-1],
            status=instance_data["status"],
            ip_address=instance_data["networkInterfaces"][0]["accessConfigs"][0].get("natIP"),
            accelerator_type=instance_data.get("guestAccelerators", [{}])[0].get("acceleratorType", "").split("/")[-1],
            accelerator_count=len(instance_data.get("guestAccelerators", [])),
            boot_disk=instance_data["disks"][0]["source"].split("/")[-1] if instance_data.get("disks") else None,
        )

    def wait_for_operation(self, operation: dict, zone: str):
        while True:
            result = (
                self.compute.zoneOperations().get(project=self.project_id, zone=zone, operation=operation["name"]).execute()
            )

            if result["status"] == "DONE":
                if "error" in result:
                    raise Exception(result["error"])
                return result
