#!/bin/bash
set -e

# Load environment variables
if [ -f "/Users/samule/repo/amplifier/.env" ]; then
    set -a
    source "/Users/samule/repo/amplifier/.env"
    set +a
fi

# Activate venv and run
cd "$(dirname "$0")/.."
source .venv/bin/activate

python generators/test_generator.py "$@"
