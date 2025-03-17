import json
import logging
import os
from pathlib import Path
from google.cloud import storage

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

        for blob in bucket.list_blobs(prefix=str(cloud_path)):
            file_path = local_path / Path(blob.name)
            file_path.parent.mkdir(parents=True, exist_ok=True)
            blob.download_to_filename(file_path)
            print(f"Downloaded {blob.name} from {self.bucket_name} to {file_path}")

        return True

    def upload_to_cloud(self, path: Path) -> bool:
        bucket = self.client.bucket(self.bucket_name)

        for root, _, files in os.walk(path):
            for file in files:
                file_path = os.path.join(root, file)
                blob = bucket.blob(os.path.relpath(file_path, path))
                blob.upload_from_filename(file_path)
                print(f"Uploaded {file_path} to {self.bucket_name}/{blob.name}")

        return True

if __name__ == '__main__':
    server_parameters = ServerParameters(namespace="google_v2", server_type=ServerType.METADATA_EXTRACTION)
    gcs = GoogleCloudStorage(server_parameters, logging.getLogger())
    gcs.copy_from_cloud(Path('oh'), Path('/home/gabo/ssd/projects/ml-cloud-connector/data'))
