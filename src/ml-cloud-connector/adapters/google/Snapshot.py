from datetime import datetime
from pydantic import BaseModel


class Snapshot(BaseModel):
    name: str
    source_disk: str
    creation_time: datetime = datetime.now()
