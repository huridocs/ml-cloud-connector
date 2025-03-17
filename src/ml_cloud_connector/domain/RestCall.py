import requests
from typing import Literal, Optional, Any
from pydantic import BaseModel
from urllib.parse import urljoin


class RestCall(BaseModel):
    port: int
    endpoint: list[str] | str
    headers: dict[str, str] = {}
    method: Literal["GET", "POST"] = "POST"
    payload: Optional[dict[str, Any]] = None
    files: Optional[dict[str, Any]] = None
    data: Optional[dict[str, Any]] = None
    timeout: int = 2000

    class Config:
        arbitrary_types_allowed = True

    def make_request(self, ip_address: str) -> Any:
        if self.endpoint and isinstance(self.endpoint, list):
            url = urljoin(f"http://{ip_address}:{self.port}", "/".join(self.endpoint))
        else:
            url = urljoin(f"http://{ip_address}:{self.port}", self.endpoint if self.endpoint else "")

        response = requests.request(
            method=self.method,
            url=url,
            headers=self.headers,
            json=self.payload if self.method != "GET" and not (self.files or self.data) else None,
            params=None if self.method != "GET" else self.payload,
            files=self.files,
            data=self.data,
            timeout=self.timeout,
        )

        response.raise_for_status()

        return response

    def __str__(self):
        return f"RestCall(endpoint={self.endpoint}, method={self.method})"