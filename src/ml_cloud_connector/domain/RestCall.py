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
    timeout: int = 30

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

        return response.json()


if __name__ == "__main__":
    # check ollama
    method = "POST"
    headers = {"Content-Type": "application/json"}
    payload = {"model": "llama3.2", "prompt": "Hello", "stream": False}
    rest_call = RestCall(port=11434, endpoint="/api/generate", headers=headers, payload=payload, method=method)
    response = rest_call.make_request(ip_address="localhost")
    print("Ollama response:", response)

    # check pdf-document-layout-analysis
    pdf_path = "~/pdf-document-layout-analysis/test_pdfs/regular.pdf"

    with open(pdf_path, "rb") as pdf_file:
        files = {"file": ("pdf_name.pdf", pdf_file, "application/pdf")}
        data = {"fast": "true"}

        rest_call = RestCall(port=5060, endpoint="/", files=files, data=data)
        response = rest_call.make_request("localhost")
        print("PDF processing response:", response)
