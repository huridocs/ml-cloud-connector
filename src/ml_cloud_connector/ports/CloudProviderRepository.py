import logging
from abc import ABC, abstractmethod

from ml_cloud_connector.domain.ServerParameters import ServerParameters


class CloudProviderRepository(ABC):
    def __init__(self, server_parameters: ServerParameters, service_logger: logging.Logger):
        self.server_parameters = server_parameters
        self.service_logger = service_logger

    @abstractmethod
    def is_properly_configured(self) -> bool:
        pass

    @abstractmethod
    def start(self) -> bool:
        pass

    @abstractmethod
    def get_ip(self) -> str:
        pass

    @abstractmethod
    def restart(self) -> bool:
        pass

    def shelve(self):
        pass
