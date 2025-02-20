from pydantic import BaseModel


class RestCall(BaseModel):
    port: int
    parameters: list[str]
    headers: dict[str, str]
    payload: dict[str, str]

