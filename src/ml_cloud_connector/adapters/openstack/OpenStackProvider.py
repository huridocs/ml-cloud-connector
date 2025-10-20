import logging
import os
import time

import openstack

from ml_cloud_connector.domain.ServerParameters import ServerParameters
from ml_cloud_connector.domain.ServerType import ServerType
from ml_cloud_connector.ports.CloudProviderRepository import CloudProviderRepository


class OpenStackProvider(CloudProviderRepository):
    def __init__(self, server_parameters: ServerParameters, service_logger: logging.Logger):
        super().__init__(server_parameters, service_logger)
        self.auth_url = os.getenv(f"AUTH_URL", "")
        self.username = os.getenv(f"USERNAME", "")
        self.password = os.getenv(f"PASSWORD", "")
        self.project_name = os.getenv(f"PROJECT_NAME", "")
        self.project_domain_name = os.getenv(f"PROJECT_DOMAIN_NAME", "default")
        self.user_domain_name = os.getenv(f"USER_DOMAIN_NAME", "default")
        self.region_name = os.getenv(f"REGION_NAME", "")
        self.instance_id = os.getenv(f"{server_parameters.namespace}INSTANCE_ID", "")
        self.conn = None
        if self.is_properly_configured():
            self.login()

    def is_properly_configured(self) -> bool:
        return all([self.auth_url, self.username, self.password, self.project_name, self.instance_id])

    def login(self):
        try:
            self.conn = openstack.connect(
                auth_url=self.auth_url,
                project_name=self.project_name,
                username=self.username,
                password=self.password,
                user_domain_name=self.user_domain_name,
                project_domain_name=self.project_domain_name,
                region_name=self.region_name,
            )
            self.service_logger.info("Successfully connected to OpenStack")
        except Exception as e:
            self.service_logger.error(f"Failed to connect to OpenStack: {str(e)}")
            raise

    def get_instance_status(self) -> str:
        try:
            server = self.conn.compute.get_server(self.instance_id)
            return server.status if server else "UNKNOWN"
        except Exception as e:
            self.service_logger.error(f"Failed to get instance status: {str(e)}")
            return "UNKNOWN"

    def start(self) -> bool:
        if not self.is_properly_configured():
            return False

        instance_status = self.get_instance_status()
        if instance_status == "SHUTOFF":
            self.service_logger.info(f"Starting the instance...")
        elif instance_status == "ACTIVE":
            return True

        try:
            self.conn.compute.start_server(self.instance_id)

            max_wait = 300
            start_time = time.time()
            while time.time() - start_time < max_wait:
                status = self.get_instance_status()
                if status == "ACTIVE":
                    return True
                elif status == "ERROR":
                    raise Exception(f"Instance entered ERROR state")
                time.sleep(2)

            raise Exception(f"Timeout waiting for instance to start")
        except Exception as e:
            self.service_logger.error(f"Failed to start instance {self.instance_id}: {str(e)}")
            return False

    def get_ip(self) -> str:
        self.service_logger.info(f"Getting instance IP...")
        try:
            server = self.conn.compute.get_server(self.instance_id)
            if not server:
                raise Exception(f"Instance {self.instance_id} not found")

            for network_name, addresses in server.addresses.items():
                for address in addresses:
                    if address.get("OS-EXT-IPS:type") == "floating" or address.get("version") == 4:
                        return address.get("addr")

            raise Exception("No IP address found for instance")
        except Exception as e:
            self.service_logger.error(f"Failed to get instance IP: {str(e)}")
            raise

    def stop(self) -> bool:
        self.service_logger.info(f"Stopping the instance...")
        try:
            self.conn.compute.stop_server(self.instance_id)

            max_wait = 300
            start_time = time.time()
            while time.time() - start_time < max_wait:
                status = self.get_instance_status()
                if status == "SHUTOFF":
                    return True
                elif status == "ERROR":
                    raise Exception(f"Instance entered ERROR state")
                time.sleep(2)

            raise Exception(f"Timeout waiting for instance to stop")
        except Exception as e:
            self.service_logger.error(f"Failed to stop instance {self.instance_id}: {str(e)}")
            return False

    def restart(self) -> bool:
        self.service_logger.info(f"Restarting the instance...")
        if self.stop():
            time.sleep(30)
            return self.start()
        return False

    @staticmethod
    def from_namespaces(
        namespaces: list[str], server_type: ServerType, service_logger: logging.Logger
    ) -> list["OpenStackProvider"]:
        providers = []
        for namespace in namespaces:
            server_parameters = ServerParameters(namespace=namespace, server_type=server_type)
            provider = OpenStackProvider(server_parameters, service_logger)
            if provider.is_properly_configured():
                providers.append(provider)
            else:
                service_logger.warning(f"OpenStackProvider with namespace {namespace} is not properly configured.")
        return providers
