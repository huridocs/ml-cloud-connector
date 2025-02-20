import requests
from typing import Literal, Optional, Any
from pydantic import BaseModel
from urllib.parse import urljoin, urlencode


class RestCall(BaseModel):
    port: int
    endpoint: str
    parameters: list[str] = []
    headers: dict[str, str] = {}
    payload: Optional[dict[str, Any]] = None

    def make_request(self, method: Literal["GET", "POST"] = "GET", timeout: int = 30) -> requests.Response:
        url = urljoin(f"http://localhost:{self.port}", self.endpoint)

        if self.parameters:
            params = {param.split("=")[0]: param.split("=")[1] for param in self.parameters if "=" in param}
            url = f"{url}?{urlencode(params)}"

        try:
            response = requests.request(
                method=method,
                url=url,
                headers=self.headers,
                json=self.payload if method != "GET" else None,
                params=None if method != "GET" else self.payload,
                timeout=timeout,
            )

            response.raise_for_status()

            return response.json()

        except requests.RequestException as e:
            raise e


if __name__ == "__main__":
    # check ollama
    headers = {"Content-Type": "application/json"}
    payload = {"model": "llama3.2", "prompt": "Hello", "stream": False}
    rest_call = RestCall(port=11434, endpoint="/api/generate", payload=payload)
    response = rest_call.make_request(method="POST")
    print(response)
