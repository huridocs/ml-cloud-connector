import time
from google.api_core.exceptions import BadRequest
from google.cloud import compute_v1
from googleapiclient.errors import HttpError

from ml_cloud_connector.wait_for_operation import wait_for_operation


class MlCloudDiskOperator:
    def __init__(self, project, service_logger):
        self.project = project
        self.service_logger = service_logger

    def disk_exists(self, compute, zone, disk_name):
        try:
            disk = compute.disks().get(project=self.project, zone=zone, disk=disk_name).execute()
            if disk:
                self.service_logger.info(f"Disk '{disk_name}' already exists in zone '{zone}'.")
                return True
        except HttpError as e:
            if e.resp.status == 404:
                self.service_logger.info(f"Disk '{disk_name}' does not exist in zone '{zone}'. Will create it.")
                return False
            else:
                self.service_logger.info(f"Error checking disk existence: {e}")
                raise
        return False

    def create_disk_from_snapshot(self, compute, target_zone, new_disk_name, snapshot_name):
        self.service_logger.info(f"Creating new disk: {new_disk_name} in zone {target_zone} from snapshot {snapshot_name}")
        disk_body = {
            "name": new_disk_name,
            "sourceSnapshot": f"projects/{self.project}/global/snapshots/{snapshot_name}",
            "type": f"projects/{self.project}/zones/{target_zone}/diskTypes/pd-ssd",
        }
        operation = compute.disks().insert(project=self.project, zone=target_zone, body=disk_body).execute()
        wait_for_operation(self.project, compute, operation, self.service_logger)

    def delete_disk(self, zone, disk_name):
        self.service_logger.info(f"Deleting disk: {disk_name} in zone {zone}")
        try:
            time.sleep(10)
            disks_client = compute_v1.DisksClient()
            operation = disks_client.delete(project=self.project, zone=zone, disk=disk_name)
            operation.result()
        except BadRequest as e:
            self.service_logger.info(f"Disk deletion [{disk_name}] failed: {e}")

    def prepare_disk(self, compute, zone, disk_name, snapshot_name):
        if not self.disk_exists(compute, zone, disk_name):
            self.create_disk_from_snapshot(compute, zone, disk_name, snapshot_name)
        else:
            self.service_logger.info(f"Using existing disk: {disk_name}")

    @staticmethod
    def get_boot_disk(instance):
        for disk in instance.get("disks", []):
            if disk.get("boot"):
                return disk["source"].split("/")[-1]
        raise Exception("Boot disk not found.")
