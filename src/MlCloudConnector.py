import time
from pathlib import Path

import ovh
import paramiko

from configuration import REGION, APP_KEY, APP_SECRET, CONSUMER_KEY, PROJECT_ID, INSTANCE_ID


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
        return instance_info["status"] == "ACTIVE"

    def start_instance(self):
        if self.is_active():
            return True

        self.client.post(f'/cloud/project/{PROJECT_ID}/instance/{INSTANCE_ID}/start')

        for i in range(100):
            if self.is_active():
                self.set_shutdown_timer()
                return True

            time.sleep(5)

    def get_instance_ip(self):
        instance_info = self.client.get(f'/cloud/project/{PROJECT_ID}/instance/{INSTANCE_ID}/')
        return instance_info["ipAddresses"][0]["ip"]

    def set_shutdown_timer(self):
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        if Path()
        ssh.connect(self.get_instance_ip(), username='root', key_filename='/local_path/to/ovh.pub')

        commands = [
            'sudo apt update',
            'sudo apt install -y docker-compose-plugin git make',
            'git clone https://github.com/huridocs/docker-translation-service.git',
            'cd docker-translation-service',
            'make start'
        ]

        for command in commands:
            stdin, stdout, stderr = ssh.exec_command(command)
            print(stdout.read().decode())