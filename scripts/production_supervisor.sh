#!/usr/bin/env bash
set -euo pipefail

# Bounded self-healing supervisor for development/staging hosts.
# Production should use systemd, Kubernetes, or a managed process platform.
export MPLBACKEND="${MPLBACKEND:-Agg}"
export DEMO_MODE="${DEMO_MODE:-false}"
export MUSIC_ENGINE_URL="${MUSIC_ENGINE_URL:-http://127.0.0.1:8001}"
export TRUST_PROXY="${TRUST_PROXY:-false}"

ACE_ROOT="${ACE_ROOT:-/content/ACE-Step-1.5}"
YATHARTH_ROOT="${YATHARTH_ROOT:-/content/yatharth-music-ai}"
ACE_PORT="${ACE_PORT:-8001}"
YATHARTH_PORT="${YATHARTH_PORT:-8000}"
HEALTH_TIMEOUT="${HEALTH_TIMEOUT:-900}"
MAX_RESTARTS="${MAX_RESTARTS:-10}"
BACKOFF_SECONDS="${BACKOFF_SECONDS:-5}"

cd "$ACE_ROOT"
mkdir -p .cache/acestep/triton .cache/acestep/torchinductor

restart_count=0
while (( restart_count < MAX_RESTARTS )); do
  echo "[supervisor] starting ACE-Step (attempt $((restart_count + 1))/$MAX_RESTARTS)"
  uv run python -m acestep.api_server --host 127.0.0.1 --port "$ACE_PORT" &
  ACE_PID=$!

  deadline=$((SECONDS + HEALTH_TIMEOUT))
  healthy=false
  while kill -0 "$ACE_PID" 2>/dev/null; do
    if curl -fsS "http://127.0.0.1:${ACE_PORT}/health" >/dev/null 2>&1; then
      healthy=true
      break
    fi
    if (( SECONDS >= deadline )); then
      echo "[supervisor] ACE-Step health timeout; restarting" >&2
      kill "$ACE_PID" 2>/dev/null || true
      break
    fi
    sleep 5
  done

  if [[ "$healthy" != "true" ]]; then
    wait "$ACE_PID" 2>/dev/null || true
    restart_count=$((restart_count + 1))
    sleep "$((BACKOFF_SECONDS * restart_count))"
    continue
  fi

  echo "[supervisor] ACE-Step healthy; starting Yatharth API"
  cd "$YATHARTH_ROOT"
  exec python -m uvicorn main:app --host 0.0.0.0 --port "$YATHARTH_PORT"
done

echo "[supervisor] restart budget exhausted; refusing to advertise availability" >&2
exit 1