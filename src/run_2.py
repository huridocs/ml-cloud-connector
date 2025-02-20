import logging
from domain.ServerType import ServerType
from adapters.google.GoogleCloudRepository import GoogleCloudRepository
from adapters.google.GoogleInstanceOperatorRepository import GoogleInstanceOperatorRepository
from adapters.google.GoogleDiskOperatorRepository import GoogleDiskOperatorRepository
from adapters.google.GoogleSnapshotOperatorRepository import GoogleSnapshotOperatorRepository
from adapters.google.GoogleCacheRepository import GoogleCacheRepository
from adapters.google.GoogleCloudConfig import GoogleCloudConfig
from ml_cloud_connector.configuration import PROJECT_ID

handlers = [logging.StreamHandler()]
logging.root.handlers = []
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s", handlers=handlers)
service_logger = logging.getLogger(__name__)


def dummy_cloud_function(message: str) -> dict:
    import socket
    import platform
    import datetime

    return {
        "message": message,
        "hostname": socket.gethostname(),
        "platform": platform.platform(),
        "timestamp": datetime.datetime.now().isoformat(),
        "success": True,
    }


def main():

    try:

        project_id = PROJECT_ID

        instance_operator = GoogleInstanceOperatorRepository(project_id, service_logger)
        disk_operator = GoogleDiskOperatorRepository(project_id, service_logger)
        snapshot_operator = GoogleSnapshotOperatorRepository(project_id, service_logger)
        cache_repository = GoogleCacheRepository()

        # remove cache
        # cache_repository.delete_instance_cache(ServerType.TRANSLATION)

        server_type = ServerType.TRANSLATION

        cloud_config = GoogleCloudConfig()

        cloud_repository = GoogleCloudRepository(
            project_id=project_id,
            server_type=server_type,
            instance_operator=instance_operator,
            disk_operator=disk_operator,
            snapshot_operator=snapshot_operator,
            cache_repository=cache_repository,
            logger=service_logger,
            config=cloud_config,
        )

        if not cloud_repository.is_active():
            service_logger.info("Starting cloud instance...")
            success = cloud_repository.start()
            if not success:
                raise Exception("Failed to start cloud instance")

        service_logger.info("Executing dummy function on cloud...")
        result, success, error_message = cloud_repository.execute_on_cloud_server(
            function=dummy_cloud_function, message="Hello from the cloud!"
        )

        service_logger.info(success)

        if success:
            service_logger.info("Function executed successfully!")
            service_logger.info(f"Result: {result}")
        else:
            service_logger.error(f"Function execution failed: {error_message}")

        if cloud_repository.is_active():
            service_logger.info("Stopping cloud instance...")
            success = cloud_repository.stop()
            if success:
                service_logger.info("Instance stopped successfully!")
            else:
                raise Exception("Failed to stop cloud instance")

    except Exception as e:
        service_logger.error(f"An error occurred: {str(e)}")
        raise


if __name__ == "__main__":
    main()
