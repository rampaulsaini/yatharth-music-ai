#!/usr/bin/env python3
"""Small dependency-free supervisor for local/free-first deployments."""
from __future__ import annotations
import argparse, os, signal, subprocess, time, urllib.request
from typing import Sequence

def healthy(url: str, timeout: float) -> bool:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            return 200 <= response.status < 500
    except Exception:
        return False

def terminate(proc: subprocess.Popen, grace: float) -> None:
    if proc.poll() is not None: return
    try:
        proc.terminate(); proc.wait(timeout=grace)
    except Exception:
        proc.kill(); proc.wait(timeout=5)

def main(argv: Sequence[str] | None = None) -> int:
    p=argparse.ArgumentParser()
    p.add_argument("--health-url", default="")
    p.add_argument("--health-timeout", type=float, default=5)
    p.add_argument("--startup-grace", type=float, default=20)
    p.add_argument("--restart-delay", type=float, default=3)
    p.add_argument("--max-restarts", type=int, default=0)
    p.add_argument("command", nargs=argparse.REMAINDER)
    a=p.parse_args(argv)
    cmd=list(a.command)
    if cmd[:1]==["--"]: cmd=cmd[1:]
    if not cmd: p.error("a child command is required")
    stop=False
    def request_stop(_signum, _frame):
        nonlocal stop; stop=True
    signal.signal(signal.SIGINT, request_stop); signal.signal(signal.SIGTERM, request_stop)
    restarts=0
    while not stop:
        proc=subprocess.Popen(cmd, env=os.environ.copy()); started=time.monotonic()
        while proc.poll() is None and not stop:
            time.sleep(2)
            if a.health_url and time.monotonic()-started >= a.startup_grace and not healthy(a.health_url,a.health_timeout):
                terminate(proc,5); break
        if stop:
            terminate(proc,5); return 0
        restarts += 1
        if a.max_restarts and restarts > a.max_restarts: return proc.returncode or 1
        time.sleep(max(0,a.restart_delay))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
