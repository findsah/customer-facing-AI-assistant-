#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${1:-http://localhost:8000}"

red() { printf "\033[31m%s\033[0m\n" "$*"; }
green() { printf "\033[32m%s\033[0m\n" "$*"; }

jq_installed() { command -v jq >/dev/null 2>&1; }

note() { printf "\n==== %s ====\n" "$*"; }

note "1) Health"
HEALTH=$(curl -s "$BASE_URL/api/health" || true)
echo "$HEALTH"

note "2) Stats"
STATS=$(curl -s "$BASE_URL/api/stats" || true)
echo "$STATS"

note "3) Ask: Internet speeds"
Q1=$(curl -s -X POST "$BASE_URL/api/ask" -H 'Content-Type: application/json' -d '{"question":"What internet speeds do you offer?"}' || true)
echo "$Q1"

note "4) Ask: Pricing"
Q2=$(curl -s -X POST "$BASE_URL/api/ask" -H 'Content-Type: application/json' -d '{"question":"How much does your service cost?"}' || true)
echo "$Q2"

note "Summary"
if jq_installed; then
  echo "$HEALTH" | jq . >/dev/null 2>&1 && green "Health OK" || red "Health FAIL"
  echo "$STATS" | jq . >/dev/null 2>&1 && green "Stats OK" || red "Stats FAIL"
  echo "$Q1" | jq . >/dev/null 2>&1 && green "Q1 OK" || red "Q1 FAIL"
  echo "$Q2" | jq . >/dev/null 2>&1 && green "Q2 OK" || red "Q2 FAIL"
else
  echo "Install jq for nicer output: sudo apt-get install -y jq"
fi
