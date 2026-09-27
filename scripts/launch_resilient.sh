#!/usr/bin/env bash
set -euo pipefail

export MPLBACKEND="${MPLBACKEND:-Agg}"
export DEMO_MODE="${DEMO_MODE:-false}"
export MUSIC_ENGINE_URL="${MUSIC_ENGINE_URL:-http://127.0.0.1:8001}"
export TRUST_PROXY="${TRUST_PROXY:-false}"

ACE_ROOT="${ACE_ROOT:-/content/ACE-Step-1.5}"
YATHARTH_ROOT="${YATHARTH_ROOT:-/content/yatharth-music-ai}"
ACE_PORT="${ACE_PORT:-8001}"
YATHARTH_PORT="${YATHARTH_PORT:-8000}"
HEALTH_TIMEOUT="${HEALTH_TIMEOUT:-900}"

cd "$ACE_ROOT"
mkdir -p .cache/acestep/triton .cache/acestep/torchinductor
uv run python -m acestep.api_server --host 127.0.0.1 --port "$ACE_PORT" &
ACE_PID=$!

cleanup() {
  kill "$ACE_PID" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

deadline=$((SECONDS + HEALTH_TIMEOUT))
until curl -fsS "http://127.0.0.1:${ACE_PORT}/health" >/dev/null 2>&1; do
  if ! kill -0 "$ACE_PID" 2>/dev/null; then
    echo "ACE-Step exited before becoming healthy." >&2
    exit 1
  fi
  if (( SECONDS >= deadline )); then
    echo "Timed out waiting for ACE-Step health." >&2
    exit 1
  fi
  sleep 5
done

cd "$YATHARTH_ROOT"
exec python -m uvicorn main:app --host 0.0.0.0 --port "$YATHARTH_PORT"
