# %% IMPORTS

import datetime
import json
import os

import google.auth
import requests
from google.cloud import iam_credentials_v1

# %% ENVIRONS

AGENT_RUN_SA = os.environ["AGENT_RUN_SA"]
AGENT_RUN_URL = os.environ["AGENT_RUN_URL"]

# %% CONFIGS

user_id = "test"
session_id = "test_123"
app_name = "search_agent"

# %% CLIENTS

credentials, project_id = google.auth.default()
iam_client = iam_credentials_v1.IAMCredentialsClient(credentials=credentials)


def get_auth_token(url: str, exp: int = 3600) -> str:
    """Gets an auth token for a given URL."""
    iat = datetime.datetime.now(tz=datetime.timezone.utc)
    exp = iat + datetime.timedelta(seconds=exp)
    jwt = {
        "aud": url,
        "iss": AGENT_RUN_SA,
        "sub": AGENT_RUN_SA,
        "iat": int(iat.timestamp()),
        "exp": int(exp.timestamp()),
    }
    payload = json.dumps(jwt)
    name = iam_client.service_account_path("-", AGENT_RUN_SA)
    response = iam_client.sign_jwt(name=name, payload=payload)
    return response.signed_jwt


# %% SESSIONS

session_url = f"{AGENT_RUN_URL}/apps/{app_name}/users/{user_id}/sessions/{session_id}"
token = get_auth_token(session_url)
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {token}",
}
session_response = requests.post(session_url, headers=headers)
print("Session creation response:")
print(session_response.status_code)
print(session_response.json())


# %% TESTS

message = "What are the latest news about Google?"
run_url = f"{AGENT_RUN_URL}/run"
token = get_auth_token(run_url)
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {token}",
}
data = {
    "user_id": user_id,
    "app_name": app_name,
    "session_id": session_id,
    "new_message": {"role": "user", "parts": [{"text": message}]},
}
response = requests.post(
    run_url,
    headers=headers,
    json=data,
)
print("Run query response:")
print(response.status_code)
print(response.json())
