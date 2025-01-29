from abc import ABC, abstractmethod
from domain.Disk import Disk


class DiskOperatorRepository(ABC):
    @abstractmethod
    def create_disk(self, disk: Disk) -> bool:
        pass

    @abstractmethod
    def delete_disk(self, zone: str, disk_name: str) -> bool:
        pass

    @abstractmethod
    def disk_exists(self, zone: str, disk_name: str) -> bool:
        pass
