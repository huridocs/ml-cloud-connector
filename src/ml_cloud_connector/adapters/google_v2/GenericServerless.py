import json
import logging
import os
import time
from pathlib import Path

import google.auth.transport.requests
import google.oauth2.id_token
import requests

from ml_cloud_connector.domain.RestCall import RestCall
from ml_cloud_connector.domain.ServerParameters import ServerParameters
from ml_cloud_connector.domain.ServerType import ServerType
from ml_cloud_connector.ports.ServerlessProviderRepository import ServerlessProviderRepository


class GenericServerless(ServerlessProviderRepository):
    TOKEN_EXPIRY_BUFFER_SECONDS = 300

    def __init__(self, server_parameters: ServerParameters, service_logger: logging.Logger):
        super().__init__(server_parameters, service_logger)
        self._id_token: str | None = None
        self._token_fetched_at: float = 0
        self.base_url = os.getenv("SERVERLESS_URL", "")
        self.login()

    @staticmethod
    def login():
        credentials = os.environ.get("CREDENTIALS", "")

        if not os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "") and credentials:
            google_application_credentials_path = Path("/", "tmp", "credentials.json")
            if isinstance(credentials, str) and '"' == credentials.strip()[0] and '"' == credentials.strip()[-1]:
                credentials = json.dumps(json.loads(credentials.strip()[1:-1]))
            google_application_credentials_path.write_text(credentials)
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str(google_application_credentials_path)

    def is_properly_configured(self) -> bool:
        return self.base_url != "" and os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "") != ""

    def _get_id_token(self) -> str:
        current_time = time.time()
        token_age = current_time - self._token_fetched_at
        token_valid = self._id_token and token_age < (3600 - self.TOKEN_EXPIRY_BUFFER_SECONDS)

        if token_valid:
            return self._id_token

        auth_req = google.auth.transport.requests.Request()
        self._id_token = google.oauth2.id_token.fetch_id_token(auth_req, self.base_url)
        self._token_fetched_at = current_time
        return self._id_token

    def make_request(self, rest_call: RestCall) -> requests.Response:
        if not self.is_properly_configured():
            raise ValueError(
                "GenericServerless is not properly configured. "
                "Set SERVERLESS_URL and GOOGLE_APPLICATION_CREDENTIALS environment variable."
            )

        id_token = self._get_id_token()
        headers = {"Authorization": f"Bearer {id_token}"}
        headers.update(rest_call.headers)

        if isinstance(rest_call.endpoint, list):
            endpoint = "/".join(rest_call.endpoint)
        else:
            endpoint = rest_call.endpoint if rest_call.endpoint else ""
        url = f"{self.base_url.rstrip('/')}/{endpoint}"

        response = requests.request(
            method=rest_call.method,
            url=url,
            headers=headers,
            json=None if rest_call.method == "GET" else rest_call.payload,
            params=rest_call.payload if rest_call.method == "GET" else None,
            files=rest_call.files,
            data=rest_call.data,
            timeout=rest_call.timeout,
        )
        response.raise_for_status()
        return response


if __name__ == "__main__":
    server_parameters = ServerParameters(namespace="google_v2", server_type=ServerType.DOCUMENT_LAYOUT_ANALYSIS)
    generic_serverless = GenericServerless(server_parameters, logging.getLogger())
    with open("document.pdf", "rb") as pdf_file:
        rest_call = RestCall(
            port=443,
            endpoint=["process"],
            files={"file": ("document.pdf", pdf_file, "application/pdf")},
            timeout=600,
        )
        response = generic_serverless.make_request(rest_call)
        print(response.json())
