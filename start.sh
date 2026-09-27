#!/usr/bin/env bash
set -euo pipefail
# Headless/server environments must not inherit notebook-only matplotlib backends.
export MPLBACKEND="${MPLBACKEND:-Agg}"
uvicorn main:app --host 0.0.0.0 --port "${PORT:-8000}"
