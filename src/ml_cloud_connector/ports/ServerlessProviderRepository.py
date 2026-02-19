import logging
from abc import ABC, abstractmethod

from ml_cloud_connector.domain.RestCall import RestCall
from ml_cloud_connector.domain.ServerParameters import ServerParameters


class ServerlessProviderRepository(ABC):
    def __init__(self, server_parameters: ServerParameters, service_logger: logging.Logger):
        self.server_parameters = server_parameters
        self.service_logger = service_logger

    @abstractmethod
    def is_properly_configured(self) -> bool:
        pass

    @abstractmethod
    def make_request(self, rest_call: RestCall):
        pass
