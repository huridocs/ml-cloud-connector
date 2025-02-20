from abc import ABC, abstractmethod
from typing import Optional
from adapters.google.GoogleCloudConfig import GoogleCloudConfig
from domain.Disk import Disk
from domain.Instance import Instance


class InstanceOperatorRepository(ABC):
    @abstractmethod
    def create_instance(self, instance_name: str, zone: str, config: GoogleCloudConfig, disk: Disk) -> Optional[Instance]:
        pass

    @abstractmethod
    def get_instance(self, zone: str, instance_id: str) -> Optional[Instance]:
        pass

    @abstractmethod
    def delete_instance(self, zone: str, instance_id: str) -> bool:
        pass

    @abstractmethod
    def start_instance(self, zone: str, instance_id: str) -> bool:
        pass

    @abstractmethod
    def stop_instance(self, zone: str, instance_id: str) -> bool:
        pass
