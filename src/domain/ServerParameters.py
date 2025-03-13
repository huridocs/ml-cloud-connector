from pydantic import BaseModel

from domain.ServerType import ServerType


class ServerParameters(BaseModel):
    namespace: str
    server_type : ServerType
