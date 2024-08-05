import time
from os.path import join

import ovh

from ml_cloud_connector.configuration import REGION, APP_KEY, APP_SECRET, CONSUMER_KEY, PROJECT_ID, INSTANCE_ID, \
    ROOT_PATH, SERVICE_PATH


class MlCloudConnector:
    def __init__(self):
        self.client = ovh.Client(
            endpoint=REGION,
            application_key=APP_KEY,
            application_secret=APP_SECRET,
            consumer_key=CONSUMER_KEY,
        )

    def is_active(self):
        instance_info = self.client.get(f'/cloud/project/{PROJECT_ID}/instance/{INSTANCE_ID}/')

        if instance_info["status"] == "ACTIVE":
            print("Instance is active")
            return True

        return False

    def start(self):
        if self.is_active():
            return True

        self.client.post(f'/cloud/project/{PROJECT_ID}/instance/{INSTANCE_ID}/start')

        for i in range(100):
            if self.is_active():
                return True

            time.sleep(5)

        return False

    def stop(self):
        if not self.is_active():
            print("Already stopped")
            return True

        self.client.post(f'/cloud/project/{PROJECT_ID}/instance/{INSTANCE_ID}/stop')

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

    def get_ip(self):
        instance_info = self.client.get(f'/cloud/project/{PROJECT_ID}/instance/{INSTANCE_ID}/')
        return instance_info["ipAddresses"][0]["ip"]

    @staticmethod
    def get_post_installation_script():
        post_installation_script = f"#!/bin/bash\n"
        with open(join(ROOT_PATH, "requirements.txt")) as f:
            requirements = f.read().splitlines()

            for requirement in requirements:
                post_installation_script += f"pip install {requirement}\n"

        automatic_shutdown_script_path = join(ROOT_PATH, 'src', 'ml_cloud_connector',
                                              "automatic_shutdown_when_no_gpu_usage.py")
        post_installation_script += f"nohup python3 {automatic_shutdown_script_path} &\n"
        post_installation_script += f"cd {SERVICE_PATH} ; make start_detached\n"
        return post_installation_script
