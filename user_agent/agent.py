"""User-facing agent that delegates search queries to a remote A2A agent."""

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

# URL to the Agent Card. See: https://google.github.io/adk-docs/a2a/quickstart-consuming/#how-it-works
# It's the entry point for the user-facing agent to discover and interact with the remote agent.
AGENT_CARD = os.getenv(
    "AGENT_CARD", f"http://localhost:8000/a2a/search_agent{AGENT_CARD_WELL_KNOWN_PATH}"
)
# Email of the calling GCP Service Account (SA)
# This is used to authenticate to the remote agent.
AGENT_RUN_SA = os.environ["AGENT_RUN_SA"]

# %% CLIENTS

# Authenticate to Google Cloud using the default credentials.
# This is necessary to use the IAM Credentials API to sign JWTs.
credentials, project_id = google.auth.default()
iam_client = iam_credentials_v1.IAMCredentialsClient(credentials=credentials)


def get_auth_token(url: str, exp: int = 3600) -> str:
    """Gets an auth token for a given URL with a expiry time (in seconds).

    The JWT contains the following claims:
    - aud: The audience of the token, which is the URL of the remote agent.
    - iss: The issuer of the token, which is the service account.
    - sub: The subject of the token, which is also the service account.
    - iat: The time the token was issued (issued at).
    - exp: The time the token expires (expiration time).

    Args:
        url: The URL of the remote agent to authenticate to.
        exp: The expiration time of the token in seconds.

    Returns:
        The signed JWT.
    """
    # Get the current time.
    iat = datetime.datetime.now(tz=datetime.timezone.utc)
    # Set the expiration time.
    exp = iat + datetime.timedelta(seconds=exp)
    # Create the JWT payload.
    jwt = {
        "aud": url,
        "iss": AGENT_RUN_SA,
        "sub": AGENT_RUN_SA,
        "iat": int(iat.timestamp()),
        "exp": int(exp.timestamp()),
    }
    # Convert the JWT to a JSON string.
    payload = json.dumps(jwt)
    # Get the full name of the service account.
    name = iam_client.service_account_path("-", AGENT_RUN_SA)
    # Sign the JWT using the IAM Credentials API.
    response = iam_client.sign_jwt(name=name, payload=payload)
    # Return the signed JWT.
    return response.signed_jwt


class BearerAuth(httpx.Auth):
    """A custom httpx authentication class that uses a bearer token."""

    def auth_flow(self, request):
        """Adds the Authorization header to the request.

        Args:
            request: The request to add the Authorization header to.

        Yields:
            The request with the Authorization header.
        """
        # Get a new auth token for the request's URL.
        token = get_auth_token(str(request.url))
        # Add the Authorization header to the request.
        request.headers["Authorization"] = f"Bearer {token}"
        # Yield the request to httpx to be sent.
        yield request


# Create an httpx client with the custom bearer authentication.
httpx_client = httpx.AsyncClient(auth=BearerAuth(), timeout=600)

# %% AGENTS


# Create a remote A2A agent that represents the remote search agent.
# This agent will delegate calls to the remote agent's tools.
search_agent = RemoteA2aAgent(
    name="search_agent",
    agent_card=AGENT_CARD,
    description="Google Search Agent",
    httpx_client=httpx_client,
)

# Create a root agent that orchestrates the interaction with the user.
# This agent will delegate search queries to the remote search agent.
root_agent = Agent(
    name="root_agent",
    model="gemini-2.5-flash",
    instruction="You are a nice and polite agent. Deleguate search query to the search_agent.",
    sub_agents=[search_agent],
)
