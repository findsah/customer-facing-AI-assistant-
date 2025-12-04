#!/usr/bin/env bash
set -euo pipefail

# Usage: ./scripts/rebuild.sh [API_BASE] [URL]
# API_BASE default: http://localhost:${API_PORT:-8000}
# URL is optional; if omitted, server uses SCRAPE_URL or default

# Load .env if present
if [[ -f .env ]]; then
  # shellcheck disable=SC1091
  source .env
fi

API_PORT=${API_PORT:-8000}
API_BASE=${1:-http://localhost:${API_PORT}}
URL=${2:-}

if [[ -n "${URL}" ]]; then
  DATA=$(jq -n --arg url "$URL" '{url: $url}')
else
  DATA='{}'
fi

echo "Rebuilding index via ${API_BASE}/api/rebuild ..."
curl -s -X POST "${API_BASE}/api/rebuild" \
  -H 'Content-Type: application/json' \
  -d "${DATA}" | jq .
