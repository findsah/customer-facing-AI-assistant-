#!/usr/bin/env bash
set -euo pipefail

# Load .env if present
if [[ -f .env ]]; then
  # shellcheck disable=SC1091
  source .env
fi

API_PORT=${API_PORT:-8000}
LOG_LEVEL=${LOG_LEVEL:-INFO}

echo "Starting API on port ${API_PORT} (LOG_LEVEL=${LOG_LEVEL})"
exec python3 -m uvicorn src.main:app --host 0.0.0.0 --port "${API_PORT}" --reload
