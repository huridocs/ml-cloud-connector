from abc import ABC, abstractmethod


class DiskOperatorRepository(ABC):
    @abstractmethod
    def create_disk(self, disk_name: str, zone: str, snapshot_name: str) -> bool:
        pass

    @abstractmethod
    def delete_disk(self, zone: str, disk_name: str) -> bool:
        pass

    @abstractmethod
    def disk_exists(self, zone: str, disk_name: str) -> bool:
        pass
