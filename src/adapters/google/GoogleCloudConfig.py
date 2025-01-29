from dataclasses import field
from pydantic import BaseModel


class GoogleCloudConfig(BaseModel):
    default_machine_type: str = "g2-standard-4"
    default_accelerator_type: str = "nvidia-l4"
    default_accelerator_count: int = 1
    network_configuration: dict = field(
        default_factory=lambda: {
            "networkInterfaces": [
                {
                    "network": "https://www.googleapis.com/compute/v1/projects/publaynet/global/networks/default",
                    "subnetwork": "https://www.googleapis.com/compute/v1/projects/publaynet/regions/europe-west4/subnetworks/default",
                    "accessConfigs": [{"type": "ONE_TO_ONE_NAT", "name": "External NAT"}],
                }
            ],
            "tags": {"items": ["http-server", "https-server", "ollama-server"], "fingerprint": "n79AIbZ_p0c="},
            "metadata": {},
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
    )
