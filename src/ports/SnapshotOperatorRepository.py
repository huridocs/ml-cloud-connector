from abc import ABC, abstractmethod
from domain.Snapshot import Snapshot


class SnapshotOperatorRepository(ABC):
    @abstractmethod
    def create_snapshot(self, snapshot: Snapshot) -> bool:
        pass

    @abstractmethod
    def snapshot_exists(self, snapshot_name: str) -> bool:
        pass