import json
import os
from pathlib import Path

from dotenv import load_dotenv
from google.auth.environment_vars import GOOGLE_CLOUD_QUOTA_PROJECT

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


GOOGLE_CLOUD_INSTANCE_CONFIGURATION = {
    "networkInterfaces": [
        {
            "network": "https://www.googleapis.com/compute/v1/projects/publaynet/global/networks/default",
            "subnetwork": "https://www.googleapis.com/compute/v1/projects/publaynet/regions/europe-west4/subnetworks/default",
            "accessConfigs": [{"type": "ONE_TO_ONE_NAT", "name": "External NAT"}],
        }
    ],
    "tags": {"items": ["http-server", "https-server", "ollama-server"], "fingerprint": "n79AIbZ_p0c="},
    "metadata": {"kind": "compute#metadata", "fingerprint": "UN94vBlYHOE="},
    "serviceAccounts": [
        {
            "email": "610489196507-compute@developer.gserviceaccount.com",
            "scopes": [
                "https://www.googleapis.com/auth/devstorage.read_only",
                "https://www.googleapis.com/auth/logging.write",
                "https://www.googleapis.com/auth/monitoring.write",
                "https://www.googleapis.com/auth/service.management.readonly",
                "https://www.googleapis.com/auth/servicecontrol",
                "https://www.googleapis.com/auth/trace.append",
            ],
        }
    ],
    "scheduling": {
        "onHostMaintenance": "TERMINATE",
        "automaticRestart": True,
        "preemptible": False,
        "provisioningModel": "STANDARD",
    },
    "labels": {},
}
