#!/usr/bin/env python3
"""Benchmark Yatharth Music AI -> ACE-Step generation time and GPU power.

Usage:
  python scripts/gpu_benchmark.py
  python scripts/gpu_benchmark.py --base-url http://127.0.0.1:8000 --durations 30,60,180

The benchmark uses the real /api/generate endpoint, so it measures the deployed
Yatharth -> ACE-Step path rather than a synthetic model call.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import threading
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass
class Sample:
    timestamp: float
    power_w: float
    memory_used_mb: float
    utilization_pct: float


@dataclass
class Result:
    duration_seconds: int
    status: str
    generation_seconds: float | None
    end_to_end_seconds: float | None
    avg_power_w: float | None
    peak_power_w: float | None
    avg_memory_used_mb: float | None
    peak_memory_used_mb: float | None
    avg_gpu_utilization_pct: float | None
    energy_wh_estimate: float | None
    energy_kwh_estimate: float | None
    electricity_cost: float | None
    error: str | None


def http_json(url: str, method: str = "GET", payload: dict[str, Any] | None = None, timeout: float = 30) -> Any:
    body = None
    headers = {"Accept": "application/json"}
    if payload is not None:
        body = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(url, data=body, headers=headers, method=method)
    with urllib.request.urlopen(request, timeout=timeout) as response:
        raw = response.read()
        return json.loads(raw.decode("utf-8")) if raw else None


def nvidia_smi_available() -> bool:
    return shutil.which("nvidia-smi") is not None


def gpu_snapshot() -> Sample | None:
    if not nvidia_smi_available():
        return None
    command = [
        "nvidia-smi",
        "--query-gpu=power.draw,memory.used,utilization.gpu",
        "--format=csv,noheader,nounits",
    ]
    try:
        output = subprocess.check_output(command, stderr=subprocess.DEVNULL, text=True, timeout=5).strip()
        line = output.splitlines()[0]
        power, memory, util = [float(x.strip()) for x in line.split(",")[:3]]
        return Sample(time.time(), power, memory, util)
    except (OSError, subprocess.SubprocessError, ValueError, IndexError):
        return None


def sampler(stop: threading.Event, samples: list[Sample], interval: float) -> None:
    while not stop.is_set():
        sample = gpu_snapshot()
        if sample:
            samples.append(sample)
        stop.wait(interval)


def mean(values: list[float]) -> float | None:
    return sum(values) / len(values) if values else None


def poll_task(base_url: str, task_id: str, timeout: float, poll: float) -> tuple[dict[str, Any], float]:
    started = time.monotonic()
    while True:
        task = http_json(f"{base_url}/api/tasks/{task_id}", timeout=20)
        status = task.get("status")
        if status in {"completed", "failed"}:
            return task, time.monotonic() - started
        if time.monotonic() - started >= timeout:
            raise TimeoutError(f"Task {task_id} exceeded benchmark timeout of {timeout:.0f}s")
        time.sleep(poll)


def run_one(base_url: str, duration: int, timeout: float, poll: float, electricity_rate: float, samples: list[Sample]) -> Result:
    payload = {
        "prompt": "cinematic uplifting Hindi instrumental, warm piano, strings, modern drums, polished original music",
        "lyrics": "",
        "language": "Hindi",
        "genre": "Cinematic",
        "mood": "Uplifting",
        "voice": "Instrumental",
        "duration": duration,
        "format": "mp3",
        "instrumental": True,
    }

    wall_start = time.monotonic()
    try:
        response = http_json(f"{base_url}/api/generate", method="POST", payload=payload, timeout=30)
        task_id = response["task_id"]
        task, generation_seconds = poll_task(base_url, task_id, timeout, poll)
        end_to_end = time.monotonic() - wall_start
        if task.get("status") != "completed":
            return Result(duration, task.get("status", "unknown"), generation_seconds, end_to_end, None, None, None, None, None, None, None, task.get("error"))
    except Exception as exc:
        return Result(duration, "error", None, time.monotonic() - wall_start, None, None, None, None, None, None, None, str(exc))

    relevant = [s for s in samples if s.timestamp >= time.time() - end_to_end - 1]
    powers = [s.power_w for s in relevant]
    memories = [s.memory_used_mb for s in relevant]
    utils = [s.utilization_pct for s in relevant]
    avg_power = mean(powers)
    peak_power = max(powers) if powers else None
    avg_memory = mean(memories)
    peak_memory = max(memories) if memories else None
    avg_util = mean(utils)
    energy_wh = (avg_power * generation_seconds / 3600) if avg_power is not None else None
    energy_kwh = energy_wh / 1000 if energy_wh is not None else None
    cost = energy_kwh * electricity_rate if energy_kwh is not None else None

    return Result(duration, "completed", generation_seconds, end_to_end, avg_power, peak_power, avg_memory, peak_memory, avg_util, energy_wh, energy_kwh, cost, None)


def print_result(result: Result) -> None:
    print(f"\n=== {result.duration_seconds}s ===")
    print(f"status:              {result.status}")
    print(f"generation time:     {result.generation_seconds:.2f}s" if result.generation_seconds is not None else "generation time:     n/a")
    print(f"end-to-end time:     {result.end_to_end_seconds:.2f}s" if result.end_to_end_seconds is not None else "end-to-end time:     n/a")
    print(f"avg GPU power:       {result.avg_power_w:.1f} W" if result.avg_power_w is not None else "avg GPU power:       n/a")
    print(f"peak GPU power:      {result.peak_power_w:.1f} W" if result.peak_power_w is not None else "peak GPU power:      n/a")
    print(f"peak VRAM:            {result.peak_memory_used_mb:.0f} MB" if result.peak_memory_used_mb is not None else "peak VRAM:            n/a")
    print(f"avg GPU utilization: {result.avg_gpu_utilization_pct:.1f}%" if result.avg_gpu_utilization_pct is not None else "avg GPU utilization: n/a")
    print(f"estimated GPU energy: {result.energy_wh_estimate:.3f} Wh" if result.energy_wh_estimate is not None else "estimated GPU energy: n/a")
    print(f"estimated electricity: ₹{result.electricity_cost:.4f}" if result.electricity_cost is not None else "estimated electricity: n/a")
    if result.error:
        print(f"error:               {result.error}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Benchmark Yatharth Music AI / ACE-Step generation")
    parser.add_argument("--base-url", default=os.getenv("YATHARTH_URL", "http://127.0.0.1:8000"))
    parser.add_argument("--durations", default="30,60,180", help="Comma-separated song lengths in seconds")
    parser.add_argument("--timeout", type=float, default=600, help="Maximum seconds per generation")
    parser.add_argument("--poll", type=float, default=2.0, help="Task polling interval")
    parser.add_argument("--electricity-rate", type=float, default=8.0, help="₹ per kWh; change to your actual tariff")
    parser.add_argument("--output", default="gpu_benchmark_results.json")
    args = parser.parse_args()

    base_url = args.base_url.rstrip("/")
    durations = [int(x.strip()) for x in args.durations.split(",") if x.strip()]
    if not durations:
        parser.error("At least one duration is required")

    health = http_json(f"{base_url}/api/health", timeout=15)
    if health.get("demo_mode"):
        raise SystemExit("ERROR: Yatharth is in DEMO_MODE. Set DEMO_MODE=false and connect ACE-Step first.")
    if not health.get("engine_reachable"):
        raise SystemExit(f"ERROR: ACE-Step is not reachable: {health}")

    print("Yatharth Music AI GPU benchmark")
    print(f"Endpoint: {base_url}")
    print(f"Durations: {durations}s")
    print(f"Electricity rate: ₹{args.electricity_rate:.2f}/kWh")
    print(f"nvidia-smi: {'available' if nvidia_smi_available() else 'not available (timing only)'}")
    print("Run sequentially; batch_size is controlled by the ACE-Step server and should be 1 for capacity benchmarking.\n")

    all_samples: list[Sample] = []
    stop = threading.Event()
    thread = threading.Thread(target=sampler, args=(stop, all_samples, 0.5), daemon=True)
    thread.start()
    results: list[Result] = []
    try:
        for duration in durations:
            result = run_one(base_url, duration, args.timeout, args.poll, args.electricity_rate, all_samples)
            results.append(result)
            print_result(result)
    finally:
        stop.set()
        thread.join(timeout=2)

    completed = [r for r in results if r.status == "completed" and r.generation_seconds]
    if completed:
        total_gen = sum(r.generation_seconds for r in completed if r.generation_seconds)
        total_duration = sum(r.duration_seconds for r in completed)
        realtime_factor = total_gen / total_duration if total_duration else None
        print("\n=== Capacity planning ===")
        print(f"generation time / audio second: {realtime_factor:.4f}x" if realtime_factor is not None else "generation time / audio second: n/a")
        if realtime_factor:
            print(f"theoretical sequential audio hours/day at 24h GPU use: {24 / realtime_factor:.2f}")
            print("Use queueing and downtime margins before selling capacity; do not treat the theoretical number as guaranteed users.")

    report = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "base_url": base_url,
        "electricity_rate_inr_per_kwh": args.electricity_rate,
        "gpu_monitoring": nvidia_smi_available(),
        "results": [asdict(r) for r in results],
        "notes": [
            "Generation timing is measured through the real Yatharth API task lifecycle.",
            "GPU energy is an estimate based on nvidia-smi power.draw samples and generation time; it excludes CPU, PSU, storage, networking and cooling overhead.",
            "For business planning, benchmark at the exact ACE-Step model/settings and with batch_size=1.",
        ],
    }
    Path(args.output).write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"\nSaved JSON report: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
