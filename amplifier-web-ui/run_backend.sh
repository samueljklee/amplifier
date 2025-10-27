#!/bin/bash
cd "$(dirname "$0")/backend"
export PYTHONPATH="$(pwd)"
uv run uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
