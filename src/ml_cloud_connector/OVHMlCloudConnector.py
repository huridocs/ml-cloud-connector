import tempfile
import time
from pathlib import Path

import ovh
import requests

from ml_cloud_connector.configuration import REGION, APP_KEY, APP_SECRET, CONSUMER_KEY, PROJECT_ID, INSTANCE_ID


class MlCloudConnector:
    IP_CACHE_PATH = Path(tempfile.gettempdir(), f"{INSTANCE_ID}.txt")

    def __init__(self):
        self.client = None
        if APP_KEY and APP_SECRET and CONSUMER_KEY:
            self.client = ovh.Client(
                endpoint=REGION,
                application_key=APP_KEY,
                application_secret=APP_SECRET,
                consumer_key=CONSUMER_KEY,
            )

    def is_active(self):
        instance_info = self.client.get(f"/cloud/project/{PROJECT_ID}/instance/{INSTANCE_ID}/")

        if instance_info["status"] == "ACTIVE":
            print("Instance is active")
            return True

        return False

    def start(self):
        if self.is_active():
            return True

        self.ovh_request("start")

        for i in range(100):
            if self.is_active():
                return True

            time.sleep(5)

        return False

    def ovh_request(self, action: str):
        for i in range(3):
            try:
                self.client.post(f"/cloud/project/{PROJECT_ID}/instance/{INSTANCE_ID}/{action}")
                break
            except ovh.exceptions.ResourceConflictError:
                time.sleep(5)

    def stop(self):
        if not self.is_active():
            print("Already stopped")
            return True

        self.ovh_request("stop")

        for i in range(100):
            if not self.is_active():
                print("stopped")
                return True

            time.sleep(5)

        return False

    def restart(self):
        if not self.stop():
            return False

        return self.start()

    def get_ip(self, port: int = 0) -> str:
        if not self.client:
            return "localhost"

        service_running = requests.get(f"http://localhost:{port}", timeout=3).status_code == 200 if port else False

        if self.IP_CACHE_PATH.exists() and service_running:
            return self.IP_CACHE_PATH.read_text()

        if self.IP_CACHE_PATH.exists() and self.is_active():
            return self.IP_CACHE_PATH.read_text()

        if not self.start():
            raise BrokenPipeError("MlCloudConnector failed to start the instance from get ip method")

        instance_info = self.client.get(f"/cloud/project/{PROJECT_ID}/instance/{INSTANCE_ID}/")
        ip = instance_info["ipAddresses"][0]["ip"]
        self.IP_CACHE_PATH.write_text(ip)
        return ip
