"""Test for a remote agent running with Agent Engine."""

# %% IMPORTS

import os

from vertexai import agent_engines

# %% ENVIRONS

AGENT_ENGINE_ID = os.environ["AGENT_ENGINE_ID"]
AGENT_USER_ID = os.getenv("AGENT_USER_ID", "test")

# %% CONFIGS

user_id = "test"
message = "Tell me the news about Google"

# %% TESTS

engine = agent_engines.get(AGENT_ENGINE_ID)
print("Schemas:", engine.operation_schemas())

events = engine.stream_query(user_id=user_id, message=message)

for i, event in enumerate(events):
    print(f"Event {i}: {event}")
