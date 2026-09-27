# Yatharth Music AI — bounded self-healing and self-upgrading

## Reliability contract

The platform must recover automatically where recovery is deterministic, but it must never pretend that software can guarantee zero failures. The control plane therefore separates:

- **self-service** — inspect status, restart/retry recoverable work, export artifacts;
- **self-healing** — restart unhealthy workers, requeue unfinished jobs, isolate failed providers;
- **self-upgrading** — propose dependency/model/config changes, test them in CI, and promote only after gates pass;
- **self-learning** — consume only verified delivery/evidence signals, with bounded changes;
- **human gates** — publication, paid advertising, rights-sensitive media, and externally consequential actions require explicit authorization.

## Required production layers

1. API replicas behind HTTPS/CDN/WAF.
2. Durable PostgreSQL task/state store.
3. Durable queue (Redis/RQ, Celery, or equivalent).
4. Independent GPU workers for ACE-Step.
5. Persistent object storage for generated media.
6. Worker health probes and automatic replacement.
7. Circuit breakers and bounded exponential retries.
8. Idempotency keys for public generation requests.
9. Recovery/audit events for every automatic action.
10. At least one independent failover worker/provider for high-availability deployments.

## Never silently fail

A failed dependency must produce one of:

- successful bounded retry;
- safe requeue;
- explicit degraded state;
- human-visible recovery-required state.

No UI may label a generation, live stream, news feed, viewer count, advertisement delivery, or production render as live unless a real adapter/provider reports that state.

## Self-upgrade gate

An agent may propose a change, but promotion follows:

proposal → isolated branch → syntax/type/tests → security checks → integration tests → human/authorized release gate → deployment → health verification → rollback on failure.

Agents must not modify production secrets, bypass branch protection, disable CI checks, or silently deploy their own upgrades.

## 24/7 acceptance tests

- API restart while jobs are queued.
- GPU worker crash during generation.
- Duplicate client submission with the same idempotency key.
- Queue restart.
- Object-storage outage.
- One GPU host unavailable.
- Engine health degradation and recovery.
- Provider timeout/circuit-open/circuit-close.
- Rollback after a failed upgrade.
- Recovery after the control-plane process is restarted.

A passing test suite is evidence of the tested scenarios, not a mathematical guarantee of uninterrupted service.
