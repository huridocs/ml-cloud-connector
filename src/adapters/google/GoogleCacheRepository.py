import json
from pathlib import Path
import tempfile
from typing import Optional, Tuple
from domain.ServerType import ServerType
from ports.CacheRepository import CacheRepository


class GoogleCacheRepository(CacheRepository):
    def __init__(self):
        self.cache_dir = Path(tempfile.gettempdir())

    def _get_cache_path(self, server_type: ServerType) -> Path:
        return self.cache_dir / f"{server_type.value}_cloud_cache.json"

    def update_instance_cache(self, server_type: ServerType, instance_id: str, zone: str):
        cache_path = self._get_cache_path(server_type)
        cache_data = {"INSTANCE": instance_id, "ZONE": zone}
        cache_path.write_text(json.dumps(cache_data))

    def get_cached_instance(self, server_type: ServerType) -> Tuple[Optional[str], Optional[str]]:
        cache_path = self._get_cache_path(server_type)
        if cache_path.exists():
            cache_data = json.loads(cache_path.read_text())
            return cache_data.get("INSTANCE"), cache_data.get("ZONE")
        return None, None

    def delete_instance_cache(self, server_type: ServerType):
        cache_path = self._get_cache_path(server_type)
        if cache_path.exists():
            cache_path.unlink()
