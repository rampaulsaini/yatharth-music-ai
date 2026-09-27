# Colab / ACE-Step startup resilience

The Yatharth API can remain healthy while the ACE-Step engine is unavailable. The UI must therefore distinguish **API online** from **engine ready**.

## Known failure from the 2026-09-27 test
ACE-Step exited during import because the notebook inherited:

`MPLBACKEND=module://matplotlib_inline.backend_inline`

ACE-Step is a server process, so use a headless backend before launching it:

```bash
export MPLBACKEND=Agg
uv run python -m acestep.api_server --host 127.0.0.1 --port 8001
```

Then wait for the engine health/readiness endpoint before opening the public tunnel.

## GPU reality
If `nvidia-smi` is unavailable, the free runtime has no NVIDIA GPU at that moment. Do not treat a public tunnel as proof that AI generation is ready. Keep the API available in fallback/demo mode and report engine_unreachable explicitly.

## Permanent-service rule
Colab + a temporary trycloudflare URL is a test environment, not permanent hosting. Production requires a durable compute provider, persistent storage, queueing, health checks and a fallback provider.
