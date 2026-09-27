#!/usr/bin/env python3
"""Bounded 24/7 supervisor for Yatharth Music AI.

This process does not perform arbitrary self-modifying code. It observes health,
records recovery intent, and exits non-zero when an external orchestrator should
replace/restart the unhealthy workload.
"""

from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

HEALTH_URL = os.getenv("YATHARTH_HEALTH_URL", "http://127.0.0.1:8000/api/health")
READY_URL = os.getenv("YATHARTH_READY_URL", "http://127.0.0.1:8000/api/ready")
TIMEOUT = float(os.getenv("HEALTH_TIMEOUT_SECONDS", "5"))
MAX_FAILURES = max(1, int(os.getenv("HEALTH_MAX_FAILURES", "3")))
STATE_FILE = Path(os.getenv("HEALTH_STATE_FILE", "runtime-health.json"))


def probe(url: str) -> tuple[bool, str]:
    try:
        with urllib.request.urlopen(url, timeout=TIMEOUT) as response:
            body = response.read().decode("utf-8", errors="replace")
            return response.status < 500, body
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        return False, str(exc)


def main() -> int:
    failures = 0
    last = {}
    while True:
        health_ok, health_body = probe(HEALTH_URL)
        ready_ok, ready_body = probe(READY_URL)
        if health_ok:
            failures = 0
        else:
            failures += 1

        last = {
            "timestamp": time.time(),
            "health_ok": health_ok,
            "ready_ok": ready_ok,
            "consecutive_failures": failures,
            "health": health_body[-2000:],
            "ready": ready_body[-2000:],
            "action": "continue" if failures < MAX_FAILURES else "replace_or_restart"
        }
        STATE_FILE.write_text(json.dumps(last, indent=2) + "\n", encoding="utf-8")

        if failures >= MAX_FAILURES:
            print(json.dumps(last), file=sys.stderr)
            return 2

        time.sleep(max(2.0, float(os.getenv("HEALTH_INTERVAL_SECONDS", "15"))))


if __name__ == "__main__":
    raise SystemExit(main())
