import time
from datetime import datetime
import socket
from logging import Logger
from typing import Callable, Any, Optional
from google.api_core.exceptions import NotFound, GoogleAPICallError
from googleapiclient import discovery
from requests.exceptions import ConnectionError
from httpx import ConnectTimeout, HTTPStatusError, ReadTimeout
from adapters.google import GoogleInstanceOperatorRepository
from adapters.google.GoogleCacheRepository import GoogleCacheRepository
from adapters.google.GoogleCloudConfig import GoogleCloudConfig
from adapters.google.GoogleDiskOperatorRepository import GoogleDiskOperatorRepository
from adapters.google.GoogleSnapshotOperatorRepository import GoogleSnapshotOperatorRepository
from domain.Disk import Disk
from domain.Instance import Instance
from domain.ServerType import ServerType
from ports.CloudProviderRepository import CloudProviderRepository


class GoogleCloudRepository(CloudProviderRepository):
    MAX_RECONNECT_TRIALS = 10
    MAX_REQUEST_TRIALS = 20
    RETRY_WAIT_TIME = 30
    MAX_WAIT_TIME = 900
    INITIAL_WAIT_TIME = 150

    def __init__(
        self,
        project_id: str,
        server_type: ServerType,
        instance_operator: GoogleInstanceOperatorRepository,
        disk_operator: GoogleDiskOperatorRepository,
        snapshot_operator: GoogleSnapshotOperatorRepository,
        cache_repository: GoogleCacheRepository,
        logger: Logger,
        config: Optional[GoogleCloudConfig] = None,
    ):
        self.project_id = project_id
        self.server_type = server_type
        self.instance_operator = instance_operator
        self.disk_operator = disk_operator
        self.snapshot_operator = snapshot_operator
        self.cache_service = cache_repository
        self.logger = logger
        self.config = config or GoogleCloudConfig()
        self.current_instance = None
        self._initialize_from_cache()

    def _initialize_from_cache(self):
        instance_id, zone = self.cache_service.get_cached_instance(self.server_type)
        if instance_id and zone:
            instance = self.instance_operator.get_instance(zone, instance_id)
            if instance:
                self.current_instance = instance
            else:
                self.forget_cloud_instance()

    def start(self) -> bool:
        self.logger.info(f"Starting the instance...")
        try:
            if not self.current_instance:
                return self.handle_instance_switch()

            if self.current_instance.status == "RUNNING":
                return True

            success = self.instance_operator.start_instance(self.current_instance.zone, self.current_instance.id)

            if success:
                self.current_instance = self.instance_operator.get_instance(
                    self.current_instance.zone, self.current_instance.id
                )
                self.logger.info("Instance started successfully!")
                return True

            return False

        except Exception as e:
            self.logger.error(f"Failed to start instance: {str(e)}")
            return False

    def stop(self) -> bool:
        self.logger.info(f"Stopping the instance...")
        try:
            if not self.current_instance:
                return True

            if self.current_instance.status != "RUNNING":
                return True

            success = self.instance_operator.stop_instance(self.current_instance.zone, self.current_instance.id)

            if success:
                self.current_instance = self.instance_operator.get_instance(
                    self.current_instance.zone, self.current_instance.id
                )
                self.logger.info("Instance stopped successfully!")
                return True

            return False

        except Exception as e:
            self.logger.error(f"Failed to stop instance: {str(e)}")
            return False

    def restart(self) -> bool:
        self.logger.info(f"Restarting the instance...")
        if self.stop():
            time.sleep(30)
            return self.start()
        return False

    def get_ip(self) -> str:
        self.logger.info(f"Getting instance IP...")
        try:
            if not self.current_instance:
                if not self.handle_instance_switch():
                    raise Exception("Failed to create or switch to a new instance")

            if not self.current_instance.ip_address:
                self.current_instance = self.instance_operator.get_instance(
                    self.current_instance.zone, self.current_instance.id
                )

            return self.current_instance.ip_address

        except Exception as e:
            self.logger.error(f"Failed to get instance IP: {str(e)}")
            raise

    def is_active(self) -> bool:
        try:
            if not self.current_instance:
                return False

            instance = self.instance_operator.get_instance(self.current_instance.zone, self.current_instance.id)
            self.logger.info("Instance is active")
            return instance is not None and instance.status == "RUNNING"

        except Exception as e:
            self.logger.error(f"Failed to check instance status: {str(e)}")
            return False

    def execute_on_cloud_server(self, function: Callable, *args, **kwargs) -> tuple[Any, bool, str]:

        if not self.get_ip():
            return None, False, "Could not get server IP"

        connection_wait_time = 0
        reconnect_trial_count = 0
        request_trial_count = 0
        self.logger.info(f"Executing function on cloud server...")
        while reconnect_trial_count < self.MAX_RECONNECT_TRIALS:
            try:
                return_value = function(*args, **kwargs)
                return return_value, True, ""

            except (ReadTimeout, ConnectionError) as e:
                if request_trial_count == self.MAX_REQUEST_TRIALS:
                    return None, False, "Response timeout"
                self.logger.warning(f"{str(e)} Retrying... [Trial: {request_trial_count + 1}]")
                time.sleep(self.RETRY_WAIT_TIME)
                request_trial_count += 1

            except (ConnectTimeout, HTTPStatusError) as e:
                self.logger.error(f"{str(e)} Retrying... [Trial: {reconnect_trial_count + 1}]")
                self.stop()
                time.sleep(connection_wait_time)
                connection_wait_time = min(connection_wait_time * 1.5 or self.INITIAL_WAIT_TIME, self.MAX_WAIT_TIME)
                self.handle_instance_switch()
                reconnect_trial_count += 1

            except NotFound:
                self.logger.info("Instance not found. Switching to new instance.")
                self.handle_instance_switch()

            except Exception as e:
                raise Exception(f"Error executing function: {str(e)}")

        return None, False, "Server error after maximum retries"

    def handle_instance_switch(self) -> bool:
        self.logger.info(f"Switching to new instance...")
        try:
            new_instance = self.create_new_instance()
            if new_instance:
                self.update_instance_details(new_instance)
                self.logger.info("Instance switch finished successfully!")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Failed to switch instance: {str(e)}")
            return False

    def create_new_instance(self) -> Optional[Instance]:
        self.logger.info(f"Creating a new instance...")
        snapshot_name = f"{self.server_type.value}-server-snapshot"
        available_zones = self.get_available_zones()
        if not available_zones:
            self.logger.error("No available zones found")
            return None

        for zone in available_zones:
            try:
                current_time = datetime.now().strftime("%Y%m%d-%H%M%S")
                hostname = socket.gethostname()
                instance_name = f"{self.server_type.value}-instance-{hostname}-{current_time}"
                if not self.snapshot_operator.snapshot_exists(snapshot_name):
                    boot_disk = self.disk_operator.get_boot_disk(self.current_instance.zone, self.current_instance.id)
                    if not self.snapshot_operator.create_initial_snapshot(snapshot_name, self.current_instance, boot_disk):
                        continue

                self.logger.info(f"Creating disk...")
                disk_name = f"disk-{instance_name}"
                disk = self.disk_operator.create_disk(disk_name, zone, snapshot_name)
                if not disk:
                    continue

                new_instance = self.instance_operator.create_instance(name=instance_name, zone=zone, config=self.config, disk=disk)

                self.logger.info(f"Successfully created instance in zone {zone}")
                return new_instance

            except GoogleAPICallError as e:
                self.logger.warning(f"Failed to create instance in zone {zone}: {str(e)}")
                self.cleanup_resources(zone, disk)
                continue
            except Exception as e:
                self.logger.error(f"Unexpected error creating instance in zone {zone}: {str(e)}")
                self.cleanup_resources(zone, disk)
                continue

        return None

    def is_zone_available(self, compute, zone_name: str, accelerator_type: str, machine_type: str) -> bool:
        try:
            accelerator_types = compute.acceleratorTypes().list(project=self.project_id, zone=zone_name).execute()

            machine_types = compute.machineTypes().list(project=self.project_id, zone=zone_name).execute()

            has_accelerator = any(acc["name"] == accelerator_type for acc in accelerator_types.get("items", []))
            has_machine_type = any(mt["name"] == machine_type for mt in machine_types.get("items", []))

            return has_accelerator and has_machine_type

        except Exception as e:
            self.logger.warning(f"Error checking zone {zone_name}: {str(e)}")
            return False

    def get_available_zones(self) -> list[str]:
        self.logger.info(f"Getting available zones...")
        compute = discovery.build("compute", "v1")
        available_zones = []
        zones_request = compute.zones().list(project=self.project_id)

        while zones_request is not None:
            response = zones_request.execute()
            for zone in response.get("items", []):
                zone_name = zone["name"]
                if self.is_zone_available(compute, zone_name, self.config.default_accelerator_type, self.config.default_machine_type):
                    available_zones.append(zone_name)
            zones_request = compute.zones().list_next(previous_request=zones_request, previous_response=response)

        preferred_zones = [zone for zone in available_zones if zone.startswith("europe-west4")]
        other_zones = [zone for zone in available_zones if not zone.startswith("europe-west4")]

        return preferred_zones + other_zones

    def cleanup_resources(self, zone: str, disk: Optional[Disk] = None):
        self.logger.info(f"Cleaning up resources...")
        if disk:
            try:
                self.disk_operator.delete_disk(zone, disk.name)
            except Exception as e:
                self.logger.warning(f"Failed to cleanup disk {disk.name}: {str(e)}")

    def update_instance_details(self, instance: Instance):
        self.current_instance = instance
        self.cache_service.update_instance_cache(server_type=self.server_type, instance_id=instance.id, zone=instance.zone)

    def forget_cloud_instance(self):
        self.cache_service.delete_instance_cache(self.server_type)
