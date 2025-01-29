from logging import Logger
from google.cloud import compute_v1
from domain.Snapshot import Snapshot
from ports.SnapshotOperatorRepository import SnapshotOperatorRepository


class GoogleSnapshotOperatorRepository(SnapshotOperatorRepository):
    def __init__(self, project_id: str, logger: Logger):
        self.project_id = project_id
        self.logger = logger
        self.snapshots_client = compute_v1.SnapshotsClient()

    def create_snapshot(self, snapshot: Snapshot) -> bool:
        try:
            disk_client = compute_v1.DisksClient()

            operation = disk_client.create_snapshot(
                project=self.project_id,
                zone=snapshot.zone,
                disk=snapshot.source_disk,
                snapshot_resource={
                    "name": snapshot.name,
                }
            )

            operation.result()  # Wait for completion
            return True

        except Exception as e:
            self.logger.error(f"Failed to create snapshot {snapshot.name}: {str(e)}")
            return False

    def snapshot_exists(self, snapshot_name: str) -> bool:
        try:
            self.snapshots_client.get(
                project=self.project_id,
                snapshot=snapshot_name
            )
            return True

        except Exception:
            return False

    def delete_snapshot(self, snapshot_name: str) -> bool:
        try:
            operation = self.snapshots_client.delete(
                project=self.project_id,
                snapshot=snapshot_name
            )
            operation.result()
            return True

        except Exception as e:
            self.logger.error(f"Failed to delete snapshot {snapshot_name}: {str(e)}")
            return False
