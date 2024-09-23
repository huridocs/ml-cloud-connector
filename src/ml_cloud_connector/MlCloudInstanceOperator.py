import time
from google.api_core.exceptions import GoogleAPICallError
from ml_cloud_connector.wait_for_operation import wait_for_operation


class MlCloudInstanceOperator:
    def __init__(self, project, zone, instance, service_logger):
        self.project = project
        self.zone = zone
        self.instance = instance
        self.service_logger = service_logger

    def create_instance(
        self,
        compute,
        target_zone,
        new_disk_name,
        instance,
        new_instance_name,
        accelerator_type,
        machine_type,
        accelerator_count=1,
    ):

        self.service_logger.info(f"Creating new instance: {new_instance_name} in zone {target_zone}")
        machine_type_full = f"projects/{self.project}/zones/{target_zone}/machineTypes/{machine_type}"
        network_interface = instance["networkInterfaces"][0]
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
                    "network": network_interface["network"],
                    "subnetwork": network_interface.get("subnetwork"),
                    "accessConfigs": [{"type": "ONE_TO_ONE_NAT", "name": "External NAT"}],
                }
            ],
            "tags": instance.get("tags", {}),
            "metadata": instance.get("metadata", {}),
            "serviceAccounts": instance.get("serviceAccounts", []),
            "scheduling": instance.get("scheduling", {}),
            "labels": instance.get("labels", {}),
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

    def get_instance_configuration(self, compute):
        return compute.instances().get(project=self.project, zone=self.zone, instance=self.instance).execute()
