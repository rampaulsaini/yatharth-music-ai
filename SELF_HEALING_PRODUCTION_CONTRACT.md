# Self-Healing and Continuous Production Contract

## What this adds

Yatharth Music AI now supports a provider pool through `MUSIC_ENGINE_URLS`.

Example:

```env
MUSIC_ENGINE_URLS=http://gpu-a:8001,http://gpu-b:8001,http://gpu-c:8001
```

New generation requests try configured providers in order until one responds successfully. Once a task is accepted, its selected provider is persisted with the durable task record, so polling stays attached to the provider that owns that engine task.

If that provider later fails, the task enters the existing bounded retry/recovery path. A future retry can select another configured provider. Interrupted tasks are recovered after an API restart.

## 24/7 boundary

This is failover logic, not a claim of infinite uptime.

For actual continuous service:

1. Run at least two independent GPU/ACE-Step workers.
2. Put the API behind a persistent HTTPS endpoint.
3. Keep SQLite only for single-node/local deployments; use PostgreSQL for multi-replica production.
4. Use Redis/RQ, Celery, or another durable queue for multi-worker scheduling.
5. Store generated audio in durable object storage.
6. Let the container/orchestrator replace unhealthy GPU workers.
7. Monitor API liveness, readiness, provider health, queue age, retries, GPU capacity and storage.
8. Test provider loss, API restart, duplicate submissions and storage failure regularly.

## Governed self-upgrade

The system may automatically detect degradation, retry work, recover state and select a healthy provider.

Production code must **not** rewrite and deploy arbitrary new code by itself. Upgrade candidates should pass deterministic CI, security checks and a signed or explicitly approved release gate before production deployment.

That gives the system a continuous learning/improvement loop without turning self-healing into uncontrolled self-modification.

## Public interface direction

The existing Control Room, Creative Studio, Live Network, Creator/Economic Hub and Music AI surfaces can consume the same health/resilience APIs. Live news, podcast, games, animation and continuous-series features should be represented as explicit production states and provider-backed jobs; the interface must never label an external stream/render/ad as live or published unless the connected provider confirms it.

## Acceptance tests

- provider A unavailable, provider B healthy -> new task reaches B;
- provider A accepts a task, then fails -> task remains durable and retries safely;
- API restarts during processing -> task returns to the recovery queue;
- all providers unavailable -> task pauses with a visible reason instead of being falsely marked successful;
- no credentials or provider -> service remains safely unavailable rather than exposing an engine;
- deployment upgrade fails -> previous healthy release remains the rollback target.
