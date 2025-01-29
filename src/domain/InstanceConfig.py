from typing import Optional
from pydantic import BaseModel


class InstanceConfig(BaseModel):
    name: str
    machine_type: str
    accelerator_type: Optional[str]
    accelerator_count: int
    network_config: dict
    zone: str
