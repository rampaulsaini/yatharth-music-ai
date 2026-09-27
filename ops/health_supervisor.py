#!/usr/bin/env python3
"""Bounded local self-healing supervisor for Yatharth Music AI development hosts.

This restarts only configured child processes after failed health checks. It never
edits source code, secrets, model weights, or data. Production HA still requires
an external orchestrator plus durable state and independent GPU workers.
"""
from __future__ import annotations
import os, signal, subprocess, time
from urllib.request import urlopen

API_HEALTH_URL = os.getenv("YATHARTH_HEALTH_URL", "http://127.0.0.1:8000/api/ready")
ENGINE_HEALTH_URL = os.getenv("ACE_HEALTH_URL", "http://127.0.0.1:8001/health")
INTERVAL = max(5, int(os.getenv("SUPERVISOR_INTERVAL_SECONDS", "15")))
FAIL_LIMIT = max(1, int(os.getenv("SUPERVISOR_FAIL_LIMIT", "3")))
MAX_RESTARTS = max(1, int(os.getenv("SUPERVISOR_MAX_RESTARTS", "5")))
ENGINE_CMD = os.getenv("ACE_STEP_COMMAND", "").strip()

def healthy(url: str) -> bool:
    try:
        with urlopen(url, timeout=5) as response:
            return 200 <= response.status < 300
    except Exception:
        return False

def main() -> int:
    child = None
    failures = 0
    restarts = 0
    stop = False

    def handle(_sig, _frame):
        nonlocal stop
        stop = True

    signal.signal(signal.SIGTERM, handle)
    signal.signal(signal.SIGINT, handle)

    while not stop:
        api_ok = healthy(API_HEALTH_URL)
        engine_ok = healthy(ENGINE_HEALTH_URL)
        if api_ok and engine_ok:
            failures = 0
        else:
            failures += 1

        if ENGINE_CMD and not engine_ok and failures >= FAIL_LIMIT:
            if child and child.poll() is None:
                child.terminate()
                try:
                    child.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    child.kill()
            if restarts >= MAX_RESTARTS:
                print("SUPERVISOR_ESCALATION: restart budget exhausted; external alert/orchestrator required.", flush=True)
                return 2
            print("SUPERVISOR_RECOVERY: restarting ACE-Step child", flush=True)
            child = subprocess.Popen(ENGINE_CMD, shell=True)
            restarts += 1
            failures = 0

        time.sleep(INTERVAL)

    if child and child.poll() is None:
        child.terminate()
    return 0

if __name__ == "__main__":
    raise SystemExit(main())