#!/bin/bash
# Docker Entrypoint for Multi-Module Python Backend
# Supports APP_ROLE environment variable to select startup mode

set -e

ROLE="${APP_ROLE:-web}"
HOST="${HOST:-0.0.0.0}"
PORT="${PORT:-8000}"

echo "Starting backend service..."
echo "  Role: ${ROLE}"
echo "  Host: ${HOST}"
echo "  Port: ${PORT}"

# Activate virtual environment
source /app/.venv/bin/activate

case "${ROLE}" in
  web)
    echo "Running Web API server..."
    exec uvicorn application_web:app --host ${HOST} --port ${PORT}
    ;;
  task)
    echo "Running Task scheduler..."
    exec runtask
    ;;
  listener)
    echo "Running Message listener..."
    exec runlistener
    ;;
  *)
    echo "Error: Unknown APP_ROLE '${APP_ROLE}'. Must be one of: web, task, listener"
    exit 1
    ;;
esac