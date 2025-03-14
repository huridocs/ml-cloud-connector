from pydantic import BaseModel

from ml_cloud_connector.domain.ServerType import ServerType


class ServerParameters(BaseModel):
    namespace: str
    server_type: ServerType
