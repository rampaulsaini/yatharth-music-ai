# Yatharth Music AI — Production Hardening Contract

## Hard invariants
1. Liveness is not readiness. `/api/health` reports process liveness; `/api/ready` must fail when the real music engine is unavailable.
2. No public generation against a dead engine. The UI must show unavailable/degraded state rather than fabricate success.
3. Self-healing is bounded. A supervisor may restart a failed worker, but must never rewrite source code, mutate secrets, or invent output.
4. Durable recovery is external to the process. Production task state belongs in PostgreSQL or an equivalent durable store; work belongs in a durable queue; generated audio belongs in object storage.
5. High availability requires independent failure domains. Use two GPU workers/providers when loss of one host must not stop service.
6. Colab and Quick Tunnel remain development/testing infrastructure, not guaranteed 24/7 hosting.
7. Every artifact keeps an evidence state: planned, processing, completed, failed, or human-review-required.

## Required production topology
Internet → HTTPS/CDN → API replicas → durable queue → GPU worker pool → object storage/CDN.

Minimum persistent components:
- PostgreSQL: task, idempotency and recovery state
- Redis/RQ, Celery, or equivalent: durable work queue
- GPU worker A: ACE-Step
- GPU worker B: ACE-Step failover/capacity
- Object storage: generated audio and manifests
- External monitoring: API, readiness, queue age, GPU health and storage health

## Recovery tests
- API process crash
- ACE-Step process crash
- GPU worker disappearance
- duplicate submission/retry
- queue restart
- database restart
- object-storage outage
- disk-full condition
- model/cache corruption
- complete loss of one compute provider

A green health check is not proof that audio generation is correct. A successful generation requires a verifiable task result and retrievable output artifact.

## AI self-upgrading boundary
The system may observe metrics, propose changes, run isolated tests, stage a candidate build, and roll back failed candidates. It must not silently self-modify production code and deploy it without an auditable gate.

## Public studio capability contract
The interface may expose music generation, lyrics/song structure, production pipeline, podcast planning, live/broadcast control, project memory, agent status, QC/review gates, exports/manifests and provider adapters.

A control is shown as LIVE only when its real provider/backend is connected and its health/readiness contract passes. Otherwise show PLANNED, READY, DEGRADED, or PROVIDER REQUIRED.