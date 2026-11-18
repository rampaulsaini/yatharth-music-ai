"""Small dependency-free supervisor for persistent Yatharth deployments.

Use this on a real server/worker host, not as a promise of 24/7 Colab uptime.
It restarts a failed child with bounded exponential backoff and records events.
"""
from __future__ import annotations

import os
import signal
import subprocess
import time
from pathlib import Path

COMMAND = os.getenv("YATHARTH_CHILD_COMMAND", "python -m uvicorn main:app --host 0.0.0.0 --port 8000").split()
MAX_BACKOFF = max(5, int(os.getenv("SUPERVISOR_MAX_BACKOFF", "120")))
LOG = Path(os.getenv("SUPERVISOR_LOG", "data/supervisor.log"))
STOP = False

def stop(*_args):
    global STOP
    STOP = True

def record(message: str) -> None:
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open("a", encoding="utf-8") as fh:
        fh.write(f"{time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())} {message}\n")

def main() -> int:
    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    backoff = 1
    while not STOP:
        record("starting child")
        proc = subprocess.Popen(COMMAND)
        while proc.poll() is None and not STOP:
            time.sleep(2)
        if STOP and proc.poll() is None:
            proc.terminate()
            proc.wait(timeout=20)
            record("child stopped by supervisor")
            return 0
        code = proc.returncode
        record(f"child exited code={code}; restarting")
        time.sleep(backoff)
        backoff = min(MAX_BACKOFF, backoff * 2)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
