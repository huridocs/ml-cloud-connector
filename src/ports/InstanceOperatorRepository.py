from abc import ABC, abstractmethod
from typing import Optional
from domain.Disk import Disk
from domain.Instance import Instance
from domain.InstanceConfig import InstanceConfig


class InstanceOperatorRepository(ABC):
    @abstractmethod
    def create_instance(self, zone: str, config: InstanceConfig, disk: Disk) -> Optional[Instance]:
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
