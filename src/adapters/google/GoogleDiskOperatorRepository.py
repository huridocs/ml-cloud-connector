from logging import Logger
from typing import Optional

from google.api_core.exceptions import BadRequest
from google.cloud import compute_v1
from domain.Disk import Disk
from ports.DiskOperatorRepository import DiskOperatorRepository


class GoogleDiskOperatorRepository(DiskOperatorRepository):
    def __init__(self, project_id: str, logger: Logger):
        self.project_id = project_id
        self.logger = logger
        self.disks_client = compute_v1.DisksClient()

    def create_disk(self, disk_name: str, zone: str, snapshot_name: str) -> Optional[Disk]:
        try:
            disk = Disk(name=disk_name, zone=zone, source_snapshot=snapshot_name, type="pd-ssd", boot=True)
            disk_resource = compute_v1.Disk()
            disk_resource.name = disk.name
            disk_resource.type = f"projects/{self.project_id}/zones/{disk.zone}/diskTypes/{disk.type}"

            if disk.source_snapshot:
                disk_resource.source_snapshot = f"projects/{self.project_id}/global/snapshots/{disk.source_snapshot}"
            else:
                disk_resource.size_gb = 100

            operation = self.disks_client.insert(project=self.project_id, zone=disk.zone, disk_resource=disk_resource)
            operation.result()
            return disk

        except Exception as e:
            self.logger.error(f"Failed to create disk {disk_name}: {str(e)}")
            return None

    def delete_disk(self, zone: str, disk_name: str) -> bool:
        try:
            operation = self.disks_client.delete(project=self.project_id, zone=zone, disk=disk_name)
            operation.result()
            return True

        except BadRequest as e:
            self.logger.error(f"Failed to delete disk {disk_name}: {str(e)}")
            return False

    def disk_exists(self, zone: str, disk_name: str) -> bool:
        try:
            self.disks_client.get(project=self.project_id, zone=zone, disk=disk_name)
            return True

        except Exception:
            return False

    def get_boot_disk(self, zone: str, instance_id: str) -> str:
        try:
            instance_client = compute_v1.InstancesClient()
            instance = instance_client.get(project=self.project_id, zone=zone, instance=instance_id)

            for disk in instance.disks:
                if disk.boot:
                    return disk.source.split("/")[-1]

            raise Exception("Boot disk not found")

        except Exception as e:
            self.logger.error(f"Failed to get boot disk for instance {instance_id}: {str(e)}")
            raise
