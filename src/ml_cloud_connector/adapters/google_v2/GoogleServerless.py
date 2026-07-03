import json
import logging
import os
import time
from pathlib import Path
from typing import Any

import google.auth.transport.requests
import google.oauth2.id_token
import requests

from ml_cloud_connector.domain.RestCall import RestCall
from ml_cloud_connector.domain.ServerParameters import ServerParameters
from ml_cloud_connector.ports.ServerlessProviderRepository import ServerlessProviderRepository


class GoogleServerless(ServerlessProviderRepository):
    TOKEN_EXPIRY_BUFFER_SECONDS = 300

    def __init__(self, server_parameters: ServerParameters, service_logger: logging.Logger):
        super().__init__(server_parameters, service_logger)
        self._id_token: str | None = None
        self._token_fetched_at: float = 0
        self.base_url = os.getenv("GOOGLE_OLLAMA_URL", "")
        self.login()

    @staticmethod
    def login():
        credentials = os.environ.get("CREDENTIALS", "")

        if not os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "") and credentials:
            google_application_credentials_path = Path("/", "tmp", "credentials.json")
            if type(credentials) == str and '"' == credentials.strip()[0] and '"' == credentials.strip()[-1]:
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

    def make_request(self, rest_call: RestCall) -> dict[str, Any]:
        if not self.is_properly_configured():
            raise ValueError(
                "GoogleServerless is not properly configured. Set GOOGLE_OLLAMA_URL and GOOGLE_APPLICATION_CREDENTIALS environment variable."
            )

        id_token = self._get_id_token()
        headers = {"Authorization": f"Bearer {id_token}", "Content-Type": "application/json"}
        headers.update(rest_call.headers)

        if isinstance(rest_call.endpoint, list):
            endpoint = "/".join(rest_call.endpoint)
        else:
            endpoint = rest_call.endpoint if rest_call.endpoint else ""

        if rest_call.data is not None:
            data = rest_call.data if isinstance(rest_call.data, str) else json.dumps(rest_call.data)
        elif rest_call.payload is not None:
            data = json.dumps(rest_call.payload)
        else:
            data = None

        response = requests.request(
            method=rest_call.method,
            url=endpoint,
            headers=headers,
            data=data,
            timeout=rest_call.timeout,
        )
        response.raise_for_status()
        return response.json()


if __name__ == "__main__":
    server_parameters = ServerParameters(namespace="google_v2", server_type="TRANSLATIONS")
    google_serverless = GoogleServerless(server_parameters, logging.getLogger())
    raw_prompt = """Please translate the following text into {language_to_name}. Follow these guidelines:
1. Maintain the original layout and formatting.
2. Translate all text accurately without omitting any part of the content.
3. Preserve the tone and style of the original text.
4. Do not include any additional comments, notes, or explanations in the output; provide only the translated text.
5. Only translate the text between ``` and ```. Do not output any other text or character.

Here is the text to be translated:

```
{text_to_translate}
```
"""
    prompt = raw_prompt.format(language_to_name="en", text_to_translate="Esta es la biografía que se necesita traducir.")
    rest_call = RestCall(
        endpoint=[os.getenv("GOOGLE_OLLAMA_URL", ""), "/api/generate"],
        method="POST",
        data={"model": "ali6parmak/hy-mt1.5:latest", "prompt": prompt, "stream": False},
        port=8080,
    )
    response = google_serverless.make_request(rest_call)
    print(response["response"])
