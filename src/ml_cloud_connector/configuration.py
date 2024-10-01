import json
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

ROOT_PATH = Path(os.path.abspath(__file__)).parent.parent.parent

CREDENTIALS_PATH = os.environ.get("CREDENTIALS_PATH", "")
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = CREDENTIALS_PATH
CREDENTIALS = os.environ.get("CREDENTIALS", "")
PROJECT_ID = os.getenv("PROJECT_ID", "")
SERVICE_PATH = os.getenv("SERVICE_PATH", "")

if not os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "") and CREDENTIALS:
    google_application_credentials_path = Path("/", "tmp", "credentials.json")
    if type(CREDENTIALS) == str and '"' == CREDENTIALS.strip()[0] and '"' == CREDENTIALS.strip()[-1]:
        CREDENTIALS = json.dumps(json.loads(CREDENTIALS.strip()[1:-1]))
    google_application_credentials_path.write_text(CREDENTIALS)
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str(google_application_credentials_path)
