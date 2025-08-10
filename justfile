# https://just.systems/man/en/

# REQUIRES

gcloud := require("gcloud")
git := require("git")
uv := require("uv")

# SETTINGS

set dotenv-load := true
set unstable := true

# VARIABLES

AGENT := "search_agent"
CLIENT := "a2a_client"

# DEFAULTS

# display help
default:
    @just --list

# TASKS

# initialize the cloud
cloud:
    gcloud auth login --update-adc
    gcloud config set project $GOOGLE_CLOUD_PROJECT
    gcloud services enable aiplatform.googleapis.com storage.googleapis.com logging.googleapis.com monitoring.googleapis.com \
        cloudtrace.googleapis.com  artifactregistry.googleapis.com cloudbuild.googleapis.com run.googleapis.com

# deploy to agent engine
deploy-agent-engine:
    uv run adk deploy agent_engine --project=$GOOGLE_CLOUD_PROJECT --region=$GOOGLE_CLOUD_LOCATION --staging_bucket=$STAGING_BUCKET --trace_to_cloud \
        --display_name={{AGENT}} --description={{AGENT}} {{env('AGENT_ENGINE_ID', '') && "--agent_engine_id=" + env('AGENT_ENGINE_ID')}} {{AGENT}}

# deploy to cloud run
deploy-cloud-run:
    # when asked "Allow unauthenticated invocations to [search-agent] (y/N)?", answer "n"
    adk deploy cloud_run --project=$GOOGLE_CLOUD_PROJECT --region=$GOOGLE_CLOUD_LOCATION --trace_to_cloud \
    --service_name={{replace(AGENT, '_', '-')}} --app_name={{AGENT}} --with_ui --a2a {{AGENT}}

# deploy all to cloud
deploy: deploy-agent-engine deploy-cloud-run

# install the project
install:
    uv sync --all-groups

# test agent engine
test-agent-engine:
    uv run python tests/agent_engine.py

# test cloud run
test-cloud-run:
    uv run python tests/cloud_run.py

# test local
test-local:
    uv run python tests/local.py

# run all tests
test: test-agent-engine test-cloud-run test-local

# launch the web UI
web:
    uv run adk web --a2a --reload --reload_agents
