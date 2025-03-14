import logging
from ports.CloudProviderRepository import CloudProviderRepository


class StorageCloudUseCase:
    def __init__(self, cloud_provider: CloudProviderRepository, service_logger: logging.Logger):
        self.cloud_provider = cloud_provider
        self.service_logger = service_logger

    def save(self, path: str, data: any) -> bool:
        return self.cloud_provider.save(data)

    def load(self, path: str) -> list[any]:
        return self.cloud_provider.load(path)
