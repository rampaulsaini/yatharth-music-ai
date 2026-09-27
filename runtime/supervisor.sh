#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
: "$ENGINE_CMD"
: "$API_CMD"
ENGINE_URL="http://127.0.0.1:8001"
READY_URL="http://127.0.0.1:8000/api/ready"
BACKOFF_SECONDS=5
source "$ROOT/runtime/headless_env.sh"
engine_pid=""
api_pid=""
cleanup() { kill "$api_pid" "$engine_pid" 2>/dev/null || true; wait 2>/dev/null || true; }
trap cleanup TERM INT EXIT
wait_http() { url="$1"; attempts="$2"; i=0; while [ "$i" -lt "$attempts" ]; do curl -fsS --max-time 3 "$url" >/dev/null 2>&1 && return 0; i=$((i+1)); sleep 2; done; return 1; }
while true; do
  bash -lc "$ENGINE_CMD" & engine_pid="$!"
  if ! wait_http "$ENGINE_URL/health" 90; then kill "$engine_pid" 2>/dev/null || true; wait "$engine_pid" 2>/dev/null || true; sleep "$BACKOFF_SECONDS"; continue; fi
  bash -lc "$API_CMD" & api_pid="$!"
  if ! wait_http "$READY_URL" 90; then kill "$api_pid" "$engine_pid" 2>/dev/null || true; wait 2>/dev/null || true; sleep "$BACKOFF_SECONDS"; continue; fi
  while kill -0 "$engine_pid" 2>/dev/null && kill -0 "$api_pid" 2>/dev/null; do sleep 5; done
  kill "$api_pid" "$engine_pid" 2>/dev/null || true; wait 2>/dev/null || true; sleep "$BACKOFF_SECONDS"
done
