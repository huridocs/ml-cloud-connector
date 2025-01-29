import re
from typing import Optional
from pydantic import BaseModel, field_validator


class Disk(BaseModel):
    name: str
    zone: str
    source_snapshot: Optional[str] = None
    type: str = "pd-ssd"
    boot: bool = False

    @classmethod
    @field_validator('name')
    def validate_name(cls, v: str) -> str:
        pattern = r'^[a-z][-a-z0-9]{0,61}[a-z0-9]$'
        if not re.match(pattern, v):
            raise ValueError(
                "Disk name must start with a lowercase letter, "
                "contain only lowercase letters, numbers, or hyphens, "
                "be between 1-63 characters, "
                "and cannot end with a hyphen"
            )
        return v
