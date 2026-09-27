# Yatharth Music AI — Resilience Watchdog

The repository includes scripts/process_watchdog.py for free-first/local
deployments. It supervises an engine process and restarts it after process
exit or an unhealthy HTTP health endpoint.

Example:

    python scripts/process_watchdog.py --health-url http://127.0.0.1:8001/health --startup-grace 60 --restart-delay 5 -- uv run python -m acestep.api_server --host 127.0.0.1 --port 8001

This is a recovery layer, not a guarantee of uninterrupted service. For
24/7 production, an external orchestrator is still required for host, power,
kernel, GPU, network and regional failures.

Durable design:
1. API liveness/readiness.
2. Durable task state and idempotency.
3. Durable queue.
4. GPU workers with restart policy.
5. Persistent object storage.
6. Independent second worker/provider for failover.
7. External monitoring and alerting.
8. Human review gates for public publication.

No software can guarantee that a service will never fail; the goal is that
failures become detected, bounded, recoverable, and observable.
