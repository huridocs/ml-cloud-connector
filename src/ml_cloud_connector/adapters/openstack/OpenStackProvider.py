import logging
import os
import time
from functools import wraps

import openstack

from ml_cloud_connector.domain.ServerParameters import ServerParameters
from ml_cloud_connector.domain.ServerType import ServerType
from ml_cloud_connector.ports.CloudProviderRepository import CloudProviderRepository


def handle_auth_errors(func):
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        try:
            return func(self, *args, **kwargs)
        except Exception as e:
            if "authentication" in str(e).lower() or "unauthorized" in str(e).lower():
                self.service_logger.warning("Authentication error detected, attempting to reconnect...")
                self._reconnect()
                return func(self, *args, **kwargs)
            else:
                raise

    return wrapper


class OpenStackProvider(CloudProviderRepository):
    def __init__(self, server_parameters: ServerParameters, service_logger: logging.Logger):
        super().__init__(server_parameters, service_logger)
        self.auth_url = os.getenv(f"AUTH_URL", "")
        self.username = os.getenv(f"USER_NAME", "")
        self.password = os.getenv(f"PASSWORD", "")
        self.project_name = os.getenv(f"PROJECT_NAME", "")
        self.region_name = os.getenv(f"REGION_NAME", "")
        self.project_domain_name = os.getenv(f"PROJECT_DOMAIN_NAME", "default")
        self.user_domain_name = os.getenv(f"USER_DOMAIN_NAME", "default")
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

    def _reconnect(self):
        if self.conn:
            try:
                self.conn.close()
            except Exception as e:
                self.service_logger.warning(f"Error closing existing OpenStack connection: {e}")
        self.login()

    @handle_auth_errors
    def get_instance_status(self) -> str:
        server = self.conn.compute.get_server(self.instance_id)
        return server.status if server else "UNKNOWN"

    def start(self) -> bool:
        try:
            self.unshelve()
            return self.start_without_unshelve()
        except Exception as e:
            self.service_logger.warning(f"Start without unshelve failed: {e}, attempting to unshelve...")
            return self.unshelve()

    @handle_auth_errors
    def start_without_unshelve(self) -> bool:
        if not self.is_properly_configured():
            return False

        instance_status = self.get_instance_status()
        if instance_status == "SHUTOFF":
            self.service_logger.info(f"Starting the instance...")
        elif instance_status == "ACTIVE":
            return True

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

    @handle_auth_errors
    def get_ip(self) -> str:
        self.service_logger.info(f"Getting instance IP...")
        server = self.conn.compute.get_server(self.instance_id)
        if not server:
            raise Exception(f"Instance {self.instance_id} not found")

        for network_name, addresses in server.addresses.items():
            for address in addresses:
                if address.get("OS-EXT-IPS:type") == "floating" or address.get("version") == 4:
                    return address.get("addr")

        raise Exception("No IP address found for instance")

    @handle_auth_errors
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

    @handle_auth_errors
    def shelve(self) -> bool:
        self.service_logger.info(f"Shelving the instance...")
        if not self.is_properly_configured():
            return False

        self.conn.compute.shelve_server(self.instance_id)

        max_wait = 300
        start_time = time.time()
        while time.time() - start_time < max_wait:
            status = self.get_instance_status()
            if status == "SHELVED_OFFLOADED":
                self.service_logger.info(f"Instance successfully shelved")
                return True
            elif status == "ERROR":
                raise Exception(f"Instance entered ERROR state")
            time.sleep(2)

        raise Exception(f"Timeout waiting for instance to shelve")

    @handle_auth_errors
    def unshelve(self) -> bool:
        self.service_logger.info(f"Unshelving the instance...")
        if not self.is_properly_configured():
            return False

        try:
            instance_status = self.get_instance_status()
            if instance_status == "ACTIVE":
                self.service_logger.info(f"Instance is already active")
                return True
        except Exception as e:
            self.service_logger.warning(f"Could not get instance status before unshelving: {e}")

        self.conn.compute.unshelve_server(self.instance_id)

        max_wait = 300
        start_time = time.time()
        while time.time() - start_time < max_wait:
            status = self.get_instance_status()
            if status == "ACTIVE":
                self.service_logger.info(f"Instance successfully unshelved")
                return True
            elif status == "ERROR":
                raise Exception(f"Instance entered ERROR state")
            time.sleep(2)

        raise Exception(f"Timeout waiting for instance to unshelve")

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
