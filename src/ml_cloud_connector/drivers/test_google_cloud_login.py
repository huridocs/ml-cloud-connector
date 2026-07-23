import logging
import time
from pathlib import Path

from dotenv import load_dotenv

from ml_cloud_connector.adapters.google_v2.GoogleCloudStorage import GoogleCloudStorage
from ml_cloud_connector.domain.ServerParameters import ServerParameters
from ml_cloud_connector.domain.ServerType import ServerType

load_dotenv()

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
)


def test_login():
    if not GoogleCloudStorage.could_be_configured():
        print("NOT CONFIGURED: set PROJECT_ID and CREDENTIALS (or GOOGLE_APPLICATION_CREDENTIALS) in .env")
        return

    server_parameters = ServerParameters(namespace="google_v2", server_type=ServerType.METADATA_EXTRACTION)
    gcs = GoogleCloudStorage(server_parameters, logging.getLogger())

    if not gcs.is_properly_configured():
        print("NOT PROPERLY CONFIGURED: check PROJECT_ID and credentials")
        return

    start = time.time()
    test_file = Path("test_login.txt")
    test_file.write_text("login test")
    try:
        bucket = gcs.client.bucket(gcs.bucket_name)
        blob = bucket.blob("test_login/test_login.txt")
        blob.upload_from_filename(test_file)
        print(f"OK: uploaded to gs://{gcs.bucket_name}/{blob.name}")
        blob.delete()
        print(f"OK: deleted gs://{gcs.bucket_name}/{blob.name}")
    finally:
        test_file.unlink(missing_ok=True)
    print("time", round(time.time() - start, 2), "s")


if __name__ == "__main__":
    test_login()
