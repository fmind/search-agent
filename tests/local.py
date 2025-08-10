"""Test for a local agent running with `adk web`."""

# %% IMPORTS

import requests

# %% CONFIGS

user_id = "test"
session_id = "test_123"
app_name = "search_agent"

# %% SESSIONS

session_response = requests.post(
    f"http://localhost:8000/apps/{app_name}/users/{user_id}/sessions/{session_id}"
)
print("Session creation response:")
print(session_response.status_code)
print(session_response.json())

# %% TESTS

message = "What are the latest news about Google?"
headers = {
    "Content-Type": "application/json",
}
data = {
    "user_id": user_id,
    "app_name": app_name,
    "session_id": session_id,
    "new_message": {"role": "user", "parts": [{"text": message}]},
}
response = requests.post(
    "http://localhost:8000/run",
    headers=headers,
    json=data,
)
print("Run query response:")
print(response.status_code)
print(response.json())
