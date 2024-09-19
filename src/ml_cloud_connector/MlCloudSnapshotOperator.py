from googleapiclient.errors import HttpError

from ml_cloud_connector.wait_for_operation import wait_for_operation


class MlCloudSnapshotOperator:
    def __init__(self, project):
        self.project = project

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

    def create_snapshot(self, compute, zone, boot_disk, snapshot_name):
        print(f"Creating snapshot: {snapshot_name}")
        snapshot_body = {
            "name": snapshot_name,
        }
        operation = (
            compute.disks().createSnapshot(project=self.project, zone=zone, disk=boot_disk, body=snapshot_body).execute()
        )
        wait_for_operation(self.project, compute, operation)

    def prepare_snapshot(self, compute, zone, snapshot_name, boot_disk):
        if not self.snapshot_exists(compute, snapshot_name):
            self.create_snapshot(compute, zone, boot_disk, snapshot_name)
        else:
            print(f"Using existing snapshot: {snapshot_name}")
