#!/usr/bin/env python3
"""Fail-fast preflight for GPU-backed ACE-Step runs."""
import os, shutil, subprocess, sys

os.environ.setdefault("MPLBACKEND", "Agg")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

print("MPLBACKEND=", os.environ["MPLBACKEND"])
nvidia = shutil.which("nvidia-smi")
if not nvidia:
    print("GPU_STATUS=NO_NVIDIA_GPU")
    print("ACTION=enable a Colab GPU runtime or use a persistent GPU worker")
    sys.exit(2)

try:
    out = subprocess.check_output([nvidia, "--query-gpu=name,memory.total", "--format=csv,noheader"], text=True, timeout=10)
except Exception as exc:
    print("GPU_STATUS=GPU_QUERY_FAILED", exc)
    sys.exit(2)

print("GPU_STATUS=READY")
print(out.strip())
print("NEXT=launch ACE-Step only after this preflight succeeds")