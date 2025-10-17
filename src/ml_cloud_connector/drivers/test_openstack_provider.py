import logging
import time

from dotenv import load_dotenv

from ml_cloud_connector.adapters.openstack.OpenStackProvider import OpenStackProvider
from ml_cloud_connector.domain.ServerParameters import ServerParameters
from ml_cloud_connector.domain.ServerType import ServerType

load_dotenv()


def run():
    server_parameters = ServerParameters(namespace="OPENSTACK_", server_type=ServerType.METADATA_EXTRACTION)
    open_stack_provider = OpenStackProvider(server_parameters, logging.getLogger())
    start = time.time()
    print("get_ip")
    print(open_stack_provider.get_ip())
    print(open_stack_provider.get_ip())
    print(open_stack_provider.stop())
    print("time", round(time.time() - start, 2), "s")


def print_variables():
    server_parameters = ServerParameters(namespace="OPENSTACK_", server_type=ServerType.METADATA_EXTRACTION)
    open_stack_provider = OpenStackProvider(server_parameters, logging.getLogger())
    print("AUTH_URL:", open_stack_provider.auth_url)
    print("USERNAME:", open_stack_provider.username)
    print("PASSWORD:", open_stack_provider.password)
    print("PROJECT_NAME:", open_stack_provider.project_name)
    print("PROJECT_DOMAIN_NAME:", open_stack_provider.project_domain_name)
    print("USER_DOMAIN_NAME:", open_stack_provider.user_domain_name)
    print("REGION_NAME:", open_stack_provider.region_name)
    print("INSTANCE_ID:", open_stack_provider.instance_id)


if __name__ == "__main__":
    print_variables()
