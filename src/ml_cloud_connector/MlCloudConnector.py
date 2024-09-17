import logging
import tempfile
import time
import inspect
import requests
from httpx import ConnectTimeout, HTTPStatusError, ReadTimeout, RemoteProtocolError
from pathlib import Path
from typing import Callable
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

    def execute(self, function: Callable, service_logger: logging.Logger, *args, **kwargs):
        signature = inspect.signature(function)
        connection_wait_time = 180
        reconnect_trial_count = 0
        request_trial_count = 0
        while reconnect_trial_count < 10:
            try:
                bound_args = signature.bind(*args, **kwargs)
                bound_args.apply_defaults()
                return_value = function(*bound_args.args, **bound_args.kwargs)
                return return_value, True, ""
            except ReadTimeout:
                if request_trial_count == 5:
                    return "There is a problem with getting the response.", False
                service_logger.warning(f"Response timeout. Retrying... [Trial: {request_trial_count + 1}]")
                request_trial_count += 1

            except (ConnectTimeout, HTTPStatusError, RemoteProtocolError, KeyError):
                service_logger.error(f"Connection timeout. Retrying... [Trial: {reconnect_trial_count + 1}]")
                self.stop()
                time.sleep(connection_wait_time)
                connection_wait_time *= 1.5
                if connection_wait_time > 900:
                    connection_wait_time = 900
                self.start()
                time.sleep(30)
                reconnect_trial_count += 1
            except Exception as e:
                raise Exception(f"Error in executing the function: {str(e)}")
        return None, False, "Response not returned. Server error."



    def is_gpu_available(self):
        instance_info = self.client.get(project=self.project, zone=self.zone, instance=self.instance)
        return True if instance_info.guest_accelerators else False


if __name__ == '__main__':
    connector = MlCloudConnector()
    print(connector.is_gpu_available())
