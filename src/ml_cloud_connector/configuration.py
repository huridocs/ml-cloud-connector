import os
from pathlib import Path

from dotenv import load_dotenv

ROOT_PATH = Path(os.path.abspath(__file__)).parent.parent.parent

CREDENTIALS = os.environ.get("CREDENTIALS", "")

if CREDENTIALS:
    google_application_credentials_path = Path("/", "tmp", "credentials.json")
    google_application_credentials_path.write_text(CREDENTIALS)
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str(google_application_credentials_path)

load_dotenv()

SERVICE_PATH = os.getenv("SERVICE_PATH")
INSTANCE_ID = os.getenv("INSTANCE_ID")
PROJECT_ID = os.getenv("PROJECT_ID")
REGION = os.getenv("REGION")
APP_KEY = os.getenv("APP_KEY")
APP_SECRET = os.getenv("APP_SECRET")
CONSUMER_KEY = os.getenv("CONSUMER_KEY")
ZONE = os.getenv("ZONE")

PUB_KEY_PATH = Path(ROOT_PATH, "ovh.pub")
