import json
import logging
import os
import time
from pathlib import Path

from google.cloud import compute_v1
from googleapiclient import discovery

from ml_cloud_connector.domain.ServerParameters import ServerParameters
from ml_cloud_connector.domain.ServerType import ServerType
from ml_cloud_connector.ports.CloudProviderRepository import CloudProviderRepository


class GoogleV2Repository(CloudProviderRepository):
    def __init__(self, server_parameters: ServerParameters, service_logger: logging.Logger):
        super().__init__(server_parameters, service_logger)
        self.project_id = os.getenv("PROJECT_ID", "")
        self.zone = os.getenv("ZONE", "")
        self.instance_id = os.getenv("INSTANCE_ID", "")
        self.login()
        self.compute_client = compute_v1.InstancesClient()
        self.compute = discovery.build("compute", "v1")

    def login(self):
        credentials = os.environ.get("CREDENTIALS", "")

        if not os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "") and credentials:
            google_application_credentials_path = Path("/", "tmp", "credentials.json")
            if type(credentials) == str and '"' == credentials.strip()[0] and '"' == credentials.strip()[-1]:
                credentials = json.dumps(json.loads(credentials.strip()[1:-1]))
            google_application_credentials_path.write_text(credentials)
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str(google_application_credentials_path)
            # os.environ["GOOGLE_CLOUD_PROJECT"] = self.project_id

    def start(self) -> bool:
        self.service_logger.info(f"Starting the instance...")
        try:
            operation = self.compute_client.start(project=self.project_id, zone=self.zone, instance=self.instance_id)
            operation.result()
            return True
        except Exception as e:
            self.service_logger.error(f"Failed to stop instance {self.project_id}: {str(e)}")
            return False

    def get_ip(self) -> str:
        self.service_logger.info(f"Getting instance IP...")
        try:
            instance_data = (
                self.compute.instances().get(project=self.project_id, zone=self.zone, instance=self.instance_id).execute()
            )
            ip_address = instance_data["networkInterfaces"][0]["accessConfigs"][0].get("natIP")

            return ip_address

        except Exception as e:
            self.service_logger.error(f"Failed to get instance IP: {str(e)}")
            raise

    def stop(self) -> bool:
        self.service_logger.info(f"Stopping the instance...")
        try:
            operation = self.compute_client.stop(project=self.project_id, zone=self.zone, instance=self.instance_id)
            operation.result()
            return True
        except Exception as e:
            self.service_logger.error(f"Failed to stop instance {self.project_id}: {str(e)}")
            return False

    def restart(self) -> bool:
        self.service_logger.info(f"Restarting the instance...")
        if self.stop():
            time.sleep(30)
            return self.start()
        return False


if __name__ == "__main__":
    server_parameters = ServerParameters(namespace="google_v2", server_type=ServerType.DOCUMENT_LAYOUT_ANALYSIS)
    google_v2_repository = GoogleV2Repository(server_parameters, logging.getLogger())
    start = time.time()
    print("start")
    print(google_v2_repository.get_ip())
    print("time", round(time.time() - start, 2), "s")
