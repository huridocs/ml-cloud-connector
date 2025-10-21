from ml_cloud_connector.adapters.openstack.OpenStackProvider import OpenStackProvider
from ml_cloud_connector.domain.ServerParameters import ServerParameters
from ml_cloud_connector.domain.ServerType import ServerType
from ml_cloud_connector.use_cases.AutomaticShutDownUseCase import AutomaticShutDownUseCase
import logging

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
)

if __name__ == "__main__":
    server_parameters = ServerParameters(namespace="OPENSTACK_", server_type=ServerType.METADATA_EXTRACTION)
    cloud_provider = OpenStackProvider(server_parameters, logging.getLogger())
    AutomaticShutDownUseCase(cloud_provider).automatic_shutdown()
