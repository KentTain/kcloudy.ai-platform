#!/bin/bash
set -euo pipefail

cd /app
export PYTHON_SERVICE_ENV=local
export APP_CONFIG_DIR=/config

echo "=== Running backend tests ==="
uv run pytest -v --tb=short -m "not slow" "$@"
