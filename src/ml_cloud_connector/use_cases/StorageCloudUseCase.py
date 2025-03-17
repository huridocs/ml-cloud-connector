import logging

from ml_cloud_connector.ports import StorageProviderRepository


class StorageCloudUseCase:
    def __init__(self, storage_provider: StorageProviderRepository, service_logger: logging.Logger):
        self.storage_provider = storage_provider
        self.service_logger = service_logger

    def save(self, path: str, data: any) -> bool:
        return self.storage_provider.save(path, data)

    def load(self, path: str) -> list[any]:
        return self.storage_provider.load(path)
