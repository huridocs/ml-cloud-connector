import json
import logging
import tempfile
import time
import inspect
from os import remove
from requests.exceptions import ConnectionError
from googleapiclient import discovery
from httpx import ConnectTimeout, HTTPStatusError, ReadTimeout, RemoteProtocolError, ConnectError
from pathlib import Path
from typing import Callable
from google.cloud import compute_v1
from ml_cloud_connector.MlCloudDiskOperator import MlCloudDiskOperator
from ml_cloud_connector.MlCloudInstanceOperator import MlCloudInstanceOperator
from ml_cloud_connector.MlCloudSnapshotOperator import MlCloudSnapshotOperator
from ml_cloud_connector.configuration import PROJECT_ID


class MlCloudConnector:
    CLOUD_CACHE_PATH = Path(tempfile.gettempdir(), f"{PROJECT_ID}_cloud_cache.json")

    def __init__(self, server_type: str, service_logger=None, zone=None, instance=None):
        # You should loging first with gcloud auth application-default login
        self.client = compute_v1.InstancesClient()
        self.service_logger = service_logger
        self.server_type = server_type
        self.project = PROJECT_ID
        self.zone = zone
        self.instance = instance
        self.initialize_connector()

    def initialize_connector(self):
        if not self.service_logger:
            handlers = [logging.StreamHandler()]
            logging.root.handlers = []
            logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s", handlers=handlers)
            self.service_logger = logging.getLogger()
        if self.zone and self.instance and not self.CLOUD_CACHE_PATH.exists():
            self.CLOUD_CACHE_PATH.write_text(json.dumps({"ZONE": self.zone, "INSTANCE": self.instance}))
        elif not (self.zone and self.instance) and self.CLOUD_CACHE_PATH.exists():
            cache_content = json.loads(self.CLOUD_CACHE_PATH.read_text())
            self.zone = cache_content["ZONE"]
            self.instance = cache_content["INSTANCE"]
        else:
            self.service_logger.info("No cache found. Creating new instance.")
            switched = False
            while not switched:
                switched = self.switch_to_new_instance()

    def is_active(self):
        instance_info = self.client.get(project=self.project, zone=self.zone, instance=self.instance)
        if instance_info.status == "RUNNING":
            self.service_logger.info("Instance is active")
            return True
        return False

    def start_attempt_with_instance_switch(self):
        while not self.start():
            switched = self.switch_to_new_instance()
            if switched:
                self.stop()
                time.sleep(120)
            else:
                wait_time = 300
                self.service_logger.info("Switching to new instance failed on all available zones.")
                self.service_logger.info(f"The process will be restarted after {wait_time} seconds.")
                time.sleep(wait_time)

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
            self.service_logger.info("Already stopped")
            return True

        self.client.stop(project=self.project, zone=self.zone, instance=self.instance)

        for i in range(100):
            if not self.is_active():
                self.service_logger.info("stopped")
                return True
            time.sleep(5)
            self.client.stop(project=self.project, zone=self.zone, instance=self.instance)
        return False

    def restart(self):
        if not self.stop():
            return False
        return self.start()

    def is_gpu_available(self):
        instance_info = self.client.get(project=self.project, zone=self.zone, instance=self.instance)
        return True if instance_info.guest_accelerators else False

    def get_ip(self):
        if not self.client:
            return "localhost"
        self.start_attempt_with_instance_switch()
        cache_content_dict = json.loads(self.CLOUD_CACHE_PATH.read_text())
        if "IP_ADDRESS" in cache_content_dict:
            return cache_content_dict["IP_ADDRESS"]
        instance_info = self.client.get(project=self.project, zone=self.zone, instance=self.instance)
        cache_content_dict["IP_ADDRESS"] = instance_info.network_interfaces[0].access_configs[0].nat_i_p
        self.CLOUD_CACHE_PATH.write_text(json.dumps(cache_content_dict))
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

            except (ConnectError, ReadTimeout):
                if request_trial_count == 20:
                    return None, False, "There is a problem with getting the response."
                service_logger.warning(f"Response timeout. Retrying in 30 seconds.. [Trial: {request_trial_count + 1}]")
                time.sleep(30)
                request_trial_count += 1

            except (ConnectionError, ConnectTimeout, HTTPStatusError, RemoteProtocolError, KeyError):
                service_logger.error(f"Connection timeout. Retrying... [Trial: {reconnect_trial_count + 1}]")
                self.stop()
                time.sleep(connection_wait_time)
                connection_wait_time *= 1.5
                if connection_wait_time > 900:
                    connection_wait_time = 900
                self.start_attempt_with_instance_switch()
                time.sleep(30)
                reconnect_trial_count += 1
            except Exception as e:
                raise Exception(f"Error in executing the function: {str(e)}")
        return None, False, "Response not returned. Server error."

    def set_new_instance_features(self, instance_id, zone):
        self.instance = instance_id
        self.zone = zone
        self.CLOUD_CACHE_PATH.write_text(json.dumps({"INSTANCE": instance_id, "ZONE": zone}))

    def switch_to_new_instance(self):
        compute = discovery.build("compute", "v1")
        instance_operator = MlCloudInstanceOperator(self.project, self.service_logger, self.server_type)
        instance_id, zone = instance_operator.create_instance_from_snapshot(compute)
        if not instance_id:
            return False
        self.set_new_instance_features(instance_id, zone)
        return True

    def switch_to_new_instance_with_base_instance(self):
        compute = discovery.build("compute", "v1")
        disk_operator = MlCloudDiskOperator(self.project, self.service_logger)
        snapshot_operator = MlCloudSnapshotOperator(self.project, self.service_logger, self.server_type)
        instance_operator = MlCloudInstanceOperator(self.project, self.service_logger, self.server_type)
        self.stop()
        base_instance = instance_operator.get_instance_configuration(compute, self.project, self.zone, self.instance)
        boot_disk = disk_operator.get_boot_disk(base_instance)
        snapshot_operator.prepare_snapshot(compute, self.zone, boot_disk)
        instance_id, zone = instance_operator.create_instance_from_snapshot(compute)
        if not instance_id:
            return False
        self.set_new_instance_features(instance_id, zone)
        return True

    @staticmethod
    def delete_cache():
        if MlCloudConnector.CLOUD_CACHE_PATH.exists():
            remove(MlCloudConnector.CLOUD_CACHE_PATH)


if __name__ == "__main__":
    # connector = MlCloudConnector("translation")
    # connector.switch_to_new_instance()
    MlCloudConnector.delete_cache()
