import json
import logging
import os
from pathlib import Path
from google.cloud import storage
from google.cloud.storage import Bucket

from ml_cloud_connector.domain.ServerParameters import ServerParameters
from ml_cloud_connector.domain.ServerType import ServerType
from ml_cloud_connector.ports.StorageProviderRepository import StorageProviderRepository


class GoogleCloudStorage(StorageProviderRepository):
    def __init__(self, server_parameters: ServerParameters, service_logger: logging.Logger):
        super().__init__(server_parameters, service_logger)
        self.login()
        self.project_id = os.getenv("PROJECT_ID", "")
        self.client = storage.Client(project=self.project_id)
        self.bucket_name = "metadata_extractor"

    @staticmethod
    def login():
        credentials = os.environ.get("CREDENTIALS", "")

        if not os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "") and credentials:
            google_application_credentials_path = Path("/", "tmp", "credentials.json")
            if type(credentials) == str and '"' == credentials.strip()[0] and '"' == credentials.strip()[-1]:
                credentials = json.dumps(json.loads(credentials.strip()[1:-1]))
            google_application_credentials_path.write_text(credentials)
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str(google_application_credentials_path)

    def copy_from_cloud(self, cloud_path: Path, local_path: Path) -> bool:
        bucket = self.client.bucket(self.bucket_name)
        prefix = str(cloud_path) if str(cloud_path).endswith("/") else str(cloud_path) + "/"

        for blob in bucket.list_blobs(prefix=prefix):
            if blob.name.endswith("/"):
                continue

            file_path = local_path / Path(blob.name).relative_to(cloud_path.parent)
            file_path.parent.mkdir(parents=True, exist_ok=True)
            blob.download_to_filename(file_path)
            print(f"Downloaded {blob.name} from {self.bucket_name} to {file_path}")

        return True

    @staticmethod
    def create_folder_if_not_exists(bucket: Bucket, folder_path: Path):
        blobs = list(bucket.list_blobs(prefix=str(folder_path)))
        if not blobs:
            blob = bucket.blob(f"{folder_path}/")
            blob.upload_from_string("")
            print(f"Created folder {folder_path} in bucket {bucket.name}")

    def upload_to_cloud(self, parent_folder_name: str, folder_path: Path) -> bool:
        bucket = self.client.bucket(self.bucket_name)
        folder = Path(parent_folder_name, folder_path.name)
        self.create_folder_if_not_exists(bucket, folder)
        for root, _, files in os.walk(folder_path):
            for file in files:
                file_path = os.path.join(root, file)
                blob = bucket.blob(f"{folder}/{os.path.relpath(file_path, folder_path)}")
                blob.upload_from_filename(file_path)
                print(f"Uploaded {file_path} to {self.bucket_name}/{blob.name}")

        return True

    def delete_from_cloud(self, parent_folder_name: str, folder_name: str) -> bool:
        bucket = self.client.bucket(self.bucket_name)
        folder = Path(parent_folder_name, folder_name)
        blobs = bucket.list_blobs(prefix=str(folder))

        for blob in blobs:
            blob.delete()
            print(f"Deleted {blob.name} from {self.bucket_name}")

        return True

    def is_properly_configured(self) -> bool:
        return all([self.project_id, self.bucket_name, os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "")])

    @staticmethod
    def could_be_configured() -> bool:
        if not os.getenv("PROJECT_ID", ""):
            return False
        if not os.getenv("CREDENTIALS", "") and not os.getenv("GOOGLE_APPLICATION_CREDENTIALS", ""):
            return False
        return True


if __name__ == "__main__":
    server_parameters = ServerParameters(namespace="google_v2", server_type=ServerType.METADATA_EXTRACTION)
    gcs = GoogleCloudStorage(server_parameters, logging.getLogger())
    # gcs.upload_to_cloud("tenant_1", Path())
    # gcs.copy_from_cloud(Path("tenant_1", "extraction_id_2"), Path())
    gcs.delete_from_cloud("tenant_1", "extraction_id")
