import tempfile
import time
from pathlib import Path

import requests
from google.cloud import compute_v1
from ml_cloud_connector.configuration import PROJECT_ID, ZONE, INSTANCE_ID


class MlCloudConnector:
    IP_CACHE_PATH = Path(tempfile.gettempdir(), f"{INSTANCE_ID}.txt")

    def __init__(self):
        self.client = None
        if PROJECT_ID and ZONE and INSTANCE_ID:
            # You should loging first with gcloud auth application-default login
            self.client = compute_v1.InstancesClient()
            self.project = PROJECT_ID
            self.zone = ZONE
            self.instance = INSTANCE_ID

    def is_active(self):
        instance_info = self.client.get(project=self.project, zone=self.zone, instance=self.instance)
        if instance_info.status == "RUNNING":
            print("Instance is active")
            return True
        return False

    def start(self):
        if self.is_active():
            return True

        self.client.start(project=self.project, zone=self.zone, instance=self.instance)

        for i in range(100):
            if self.is_active():
                return True
            time.sleep(5)
            self.client.start(project=self.project, zone=self.zone, instance=self.instance)
        return False

    def stop(self):
        if not self.is_active():
            print("Already stopped")
            return True

        self.client.stop(project=self.project, zone=self.zone, instance=self.instance)

        for i in range(100):
            if not self.is_active():
                print("stopped")
                return True
            time.sleep(5)
            self.client.stop(project=self.project, zone=self.zone, instance=self.instance)
        return False

    def restart(self):
        if not self.stop():
            return False
        return self.start()

    def get_ip(self, port: int = 0):
        if not self.client:
            return "localhost"

        service_running = requests.get(f"http://localhost:{port}", timeout=3).status_code == 200 if port else False

        if self.IP_CACHE_PATH.exists() and service_running:
            return self.IP_CACHE_PATH.read_text()

        if self.IP_CACHE_PATH.exists() and self.is_active():
            return self.IP_CACHE_PATH.read_text()

        if not self.start():
            raise BrokenPipeError("MlCloudConnector failed to start the instance from get ip method")

        instance_info = self.client.get(project=self.project, zone=self.zone, instance=self.instance)
        return instance_info.network_interfaces[0].access_configs[0].nat_i_p

    def is_gpu_available(self):
        instance_info = self.client.get(project=self.project, zone=self.zone, instance=self.instance)
        return True if instance_info.guest_accelerators else False


if __name__ == '__main__':
    connector = MlCloudConnector()
    print(connector.is_gpu_available())
