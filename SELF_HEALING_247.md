# Yatharth Music AI — self-healing 24/7 architecture

## Hardened runtime
- Server processes force a headless matplotlib backend (Agg), preventing notebook-only backends from crashing ACE-Step imports.
- A two-process supervisor waits for engine health before API readiness and restarts the pair when either child exits.
- Liveness and readiness remain separate: a live API with an unavailable engine is not treated as ready for real generation.
- CI compiles, imports and smoke-tests the runtime in headless mode.

## Durable 24/7 architecture
A supervisor improves recovery but cannot create high availability alone. The production target is:
Public API -> durable queue -> GPU worker A/B -> object storage -> CDN
with persistent task state, worker leases/heartbeats, idempotency keys, retries and recovery history.

## Self-upgrade contract
Automatic upgrades must be bounded and reversible: discover candidate -> isolated build -> regression tests -> compare with known-good -> promote -> retain rollback. No untested agent-generated code or model is silently promoted.

## Self-service contract
Expose safe operations such as health/readiness, retry, cancel, stale-lease recovery, provider switch and rollback. Protect destructive actions and credential changes.

## Required failure drills
Engine crash, API crash, engine timeout, duplicate submission, worker restart, storage timeout and malformed provider response must be tested. Recovery must preserve attribution and never emit a false success.
