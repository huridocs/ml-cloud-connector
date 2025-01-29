import logging
from abc import ABC, abstractmethod
from typing import Callable, Any


class CloudProviderRepository(ABC):
    @abstractmethod
    def execute_on_cloud_server(self, function: Callable, logger: logging.Logger, *args, **kwargs) -> tuple[Any, bool, str]:
        pass

    @abstractmethod
    def start(self) -> bool:
        pass

    @abstractmethod
    def stop(self) -> bool:
        pass

    @abstractmethod
    def restart(self) -> bool:
        pass

    @abstractmethod
    def get_ip(self) -> str:
        pass

    @abstractmethod
    def is_active(self) -> bool:
        pass

    @abstractmethod
    def get_available_zones(self) -> list[str]:
        pass
