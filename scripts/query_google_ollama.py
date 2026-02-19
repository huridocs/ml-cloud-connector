import json
import os

import google
import google.oauth2.credentials
from google.auth import compute_engine
import google.auth.transport.requests

import requests
import google.auth.transport.requests
import google.oauth2.id_token

target_url = os.getenv("GOOGLE_OLLAMA_URL")


def make_request(method, path, data=None):
    auth_req = google.auth.transport.requests.Request()
    id_token = google.oauth2.id_token.fetch_id_token(auth_req, target_url)
    headers = {
        "Authorization": f"Bearer {id_token}",
        "Content-Type": "application/json"
    }
    response = requests.request(method, f"{target_url}{path}", data=data, headers=headers)
    return response.json()


if __name__ == '__main__':
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
    prompt = raw_prompt.format(language_to_name="Spanish", text_to_translate="please translate this text")
    data = json.dumps({
        "model": "ali6parmak/hy-mt1.5:latest",
        "prompt": prompt,
        "stream": False
    })
    response = make_request("POST", "/api/generate", data=data)
    print(response['response'])
