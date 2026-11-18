#!/usr/bin/env python3
"""Small process supervisor for a local ACE-Step API.

It deliberately supervises infrastructure, not model code: failed processes are
restarted with bounded backoff and health probes. Version upgrades remain
explicit, tested deployments rather than self-modifying production code.
"""
from __future__ import annotations

import os
import signal
import subprocess
import time
import urllib.request

HOST = os.getenv("ACE_HOST", "127.0.0.1")
PORT = int(os.getenv("ACE_PORT", "8001"))
HEALTH_URL = os.getenv("ACE_HEALTH_URL", f"http://{HOST}:{PORT}/health")
COMMAND = os.getenv(
    "ACE_STEP_COMMAND",
    f"uv run python -m acestep.api_server --host {HOST} --port {PORT}",
).split()
STARTUP_TIMEOUT = int(os.getenv("ACE_STARTUP_TIMEOUT_SECONDS", "600"))
CHECK_INTERVAL = int(os.getenv("ACE_HEALTH_INTERVAL_SECONDS", "15"))
MAX_BACKOFF = int(os.getenv("ACE_MAX_BACKOFF_SECONDS", "120"))

stopping = False


def stop(*_args: object) -> None:
    global stopping
    stopping = True


signal.signal(signal.SIGTERM, stop)
signal.signal(signal.SIGINT, stop)


def healthy() -> bool:
    try:
        with urllib.request.urlopen(HEALTH_URL, timeout=5) as response:
            return 200 <= response.status < 500
    except Exception:
        return False


def main() -> int:
    env = os.environ.copy()
    env["MPLBACKEND"] = "Agg"
    env["TOKENIZERS_PARALLELISM"] = "false"
    backoff = 2

    while not stopping:
        print(f"[supervisor] starting ACE-Step: {' '.join(COMMAND)}", flush=True)
        process = subprocess.Popen(COMMAND, env=env)
        deadline = time.time() + STARTUP_TIMEOUT

        while not stopping and time.time() < deadline:
            if process.poll() is not None:
                print(f"[supervisor] process exited with {process.returncode}", flush=True)
                break
            if healthy():
                print("[supervisor] ACE-Step healthy", flush=True)
                backoff = 2
                while not stopping and process.poll() is None:
                    time.sleep(CHECK_INTERVAL)
                    if not healthy():
                        print("[supervisor] health check failed; restarting", flush=True)
                        process.terminate()
                        try:
                            process.wait(timeout=20)
                        except subprocess.TimeoutExpired:
                            process.kill()
                            process.wait(timeout=10)
                        break
                else:
                    break
            time.sleep(4)
        else:
            if process.poll() is None:
                print("[supervisor] startup/health timeout; restarting", flush=True)
                process.terminate()
                try:
                    process.wait(timeout=20)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=10)

        if stopping:
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=20)
                except subprocess.TimeoutExpired:
                    process.kill()
            break

        print(f"[supervisor] backoff {backoff}s", flush=True)
        time.sleep(backoff)
        backoff = min(MAX_BACKOFF, backoff * 2)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
