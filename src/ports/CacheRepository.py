from abc import ABC, abstractmethod
from typing import Optional
from domain.ServerType import ServerType


class CacheRepository(ABC):
    @abstractmethod
    def update_instance_cache(self, server_type: ServerType, instance_id: str, zone: str):
        pass

    @abstractmethod
    def get_cached_instance(self, server_type: ServerType) -> tuple[Optional[str], Optional[str]]:
        pass
