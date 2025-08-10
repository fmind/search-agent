# %% IMPORTS

import datetime
import json
import os

import google.auth
import httpx
from google.adk.agents.llm_agent import Agent
from google.adk.agents.remote_a2a_agent import (
    AGENT_CARD_WELL_KNOWN_PATH,
    RemoteA2aAgent,
)
from google.cloud import iam_credentials_v1

# %% ENVIRONS

AGENT_CARD = os.getenv(
    "AGENT_CARD", f"http://localhost:8000/a2a/search_agent{AGENT_CARD_WELL_KNOWN_PATH}"
)
AGENT_RUN_SA = os.environ["AGENT_RUN_SA"]

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


class BearerAuth(httpx.Auth):
    def auth_flow(self, request):
        token = get_auth_token(str(request.url))
        request.headers["Authorization"] = f"Bearer {token}"
        yield request


httpx_client = httpx.AsyncClient(auth=BearerAuth(), timeout=600)

# %% AGENTS


search_agent = RemoteA2aAgent(
    name="search_agent",
    agent_card=AGENT_CARD,
    description="Google Search Agent",
    httpx_client=httpx_client,
)

root_agent = Agent(
    name="root_agent",
    model="gemini-2.5-flash",
    instruction="You are a nice and polite agent. Deleguate search query to the search_agent.",
    sub_agents=[search_agent],
)
