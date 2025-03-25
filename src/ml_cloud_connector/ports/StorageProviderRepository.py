import logging
from abc import ABC, abstractmethod
from pathlib import Path

from ml_cloud_connector.domain.ServerParameters import ServerParameters


class StorageProviderRepository(ABC):
    def __init__(self, server_parameters: ServerParameters, service_logger: logging.Logger):
        self.server_parameters = server_parameters
        self.service_logger = service_logger

    @abstractmethod
    def copy_from_cloud(self, cloud_path: Path, local_path: Path) -> bool:
        pass

    @abstractmethod
    def upload_to_cloud(self, folder_name: str, path: Path) -> bool:
        pass
