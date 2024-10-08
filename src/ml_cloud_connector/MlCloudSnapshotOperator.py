from googleapiclient.errors import HttpError

from ml_cloud_connector.ServerType import ServerType
from ml_cloud_connector.wait_for_operation import wait_for_operation


class MlCloudSnapshotOperator:
    def __init__(self, project, service_logger, server_type: ServerType):
        self.project = project
        self.service_logger = service_logger
        self.server_type = server_type

    def snapshot_exists(self, compute, snapshot_name):
        try:
            snapshot = compute.snapshots().get(project=self.project, snapshot=snapshot_name).execute()
            if snapshot:
                self.service_logger.info(f"Snapshot '{snapshot_name}' already exists.")
                return True
        except HttpError as e:
            if e.resp.status == 404:
                self.service_logger.info(f"Snapshot '{snapshot_name}' does not exist. Will create it.")
                return False
            else:
                self.service_logger.info(f"Error checking snapshot existence: {e}")
                raise
        return False

    def create_snapshot(self, compute, zone, boot_disk, snapshot_name):
        self.service_logger.info(f"Creating snapshot: {snapshot_name}")
        snapshot_body = {
            "name": snapshot_name,
        }
        operation = (
            compute.disks().createSnapshot(project=self.project, zone=zone, disk=boot_disk, body=snapshot_body).execute()
        )
        wait_for_operation(self.project, compute, operation, self.service_logger)

    def prepare_snapshot(self, compute, zone, boot_disk_name):
        snapshot_name = f"{self.server_type.value}-server-snapshot"
        if not self.snapshot_exists(compute, snapshot_name):
            self.create_snapshot(compute, zone, boot_disk_name, snapshot_name)
        else:
            self.service_logger.info(f"Using existing snapshot: {snapshot_name}")
