import logging
import time

from dotenv import load_dotenv

from ml_cloud_connector.adapters.openstack.OpenStackProvider import OpenStackProvider
from ml_cloud_connector.domain.ServerParameters import ServerParameters
from ml_cloud_connector.domain.ServerType import ServerType

load_dotenv()

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
)


def run():
    server_parameters = ServerParameters(namespace="OPENSTACK_", server_type=ServerType.METADATA_EXTRACTION)
    open_stack_provider = OpenStackProvider(server_parameters, logging.getLogger())
    start = time.time()
    print("get_ip")
    print(open_stack_provider.get_ip())
    print(open_stack_provider.get_ip())
    print(open_stack_provider.stop())
    print("time", round(time.time() - start, 2), "s")


def stop():
    server_parameters = ServerParameters(namespace="OPENSTACK_", server_type=ServerType.METADATA_EXTRACTION)
    open_stack_provider = OpenStackProvider(server_parameters, logging.getLogger())
    print("Stopping instance...")
    stop_result = open_stack_provider.stop()
    print(f"Stop result: {stop_result}")


def start():
    server_parameters = ServerParameters(namespace="OPENSTACK_", server_type=ServerType.METADATA_EXTRACTION)
    open_stack_provider = OpenStackProvider(server_parameters, logging.getLogger())
    print("Stopping instance...")
    stop_result = open_stack_provider.start()
    print(f"Stop result: {stop_result}")


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


def unshelve():
    server_parameters = ServerParameters(namespace="OPENSTACK_", server_type=ServerType.METADATA_EXTRACTION)
    open_stack_provider = OpenStackProvider(server_parameters, logging.getLogger())

    start = time.time()
    print("Unshelving instance...")
    unshelve_result = open_stack_provider.unshelve()
    print(f"Unshelve result: {unshelve_result}")
    unshelve_time = time.time() - start
    print(f"Unshelve time: {round(unshelve_time, 2)}s")

    ip_start = time.time()
    print("Getting IP...")
    ip_address = open_stack_provider.get_ip()
    ip_time = time.time() - ip_start
    print(f"IP address: {ip_address}")
    print(f"Time to get IP: {round(ip_time, 2)}s")

    total_time = time.time() - start
    print(f"Total time: {round(total_time, 2)}s")


def shelve():
    server_parameters = ServerParameters(namespace="OPENSTACK_", server_type=ServerType.METADATA_EXTRACTION)
    open_stack_provider = OpenStackProvider(server_parameters, logging.getLogger())

    start = time.time()
    print("Shelving instance...")
    shelve_result = open_stack_provider.shelve()
    print(f"Shelve result: {shelve_result}")
    shelve_time = time.time() - start
    print(f"Shelve time: {round(shelve_time, 2)}s")


if __name__ == "__main__":
    # print_variables()
    shelve()
    # stop()
    # unshelve()
    # start()
