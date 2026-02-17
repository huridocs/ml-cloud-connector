import os
import requests
import google.auth.transport.requests
import google.oauth2.id_token
from google.auth.transport.requests import Request
from google.oauth2 import service_account
from google.auth.impersonated_credentials import Credentials as ImpersonatedCredentials


def make_authorized_get_request(service_url):
    """
    Makes a GET request to a private Cloud Run service.
    """

    id_token = credentials.token
    # 2. Add the token to the Authorization header
    headers = {
        "Authorization": f"Bearer {id_token}"
    }

    # 3. Send the request
    response = requests.get(service_url, headers=headers)

    return response.text


if __name__ == '__main__':
    # credentials, project = gcloud_config_helper.default()
    URL = os.getenv("GOOGLE_OLLAMA_URL")
    # print(make_authorized_get_request(URL))
    _, PROJECT_ID = google.auth.default()

    print(_)
    # print(credentials.token)