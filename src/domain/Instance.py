from typing import Optional
from datetime import datetime
from pydantic import BaseModel


class Instance(BaseModel):
    id: str
    name: str
    zone: str
    machine_type: str
    status: str
    ip_address: Optional[str] = None
    accelerator_type: Optional[str] = None
    accelerator_count: int = 0
    creation_time: datetime = datetime.now()
    boot_disk: Optional[str] = None
