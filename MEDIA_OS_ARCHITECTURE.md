# Yatharth Media OS — resilience and continuous-production contract

## Goal
Provide one public interface for music, creative production, episodic storytelling, live-media adapters, product promotion and automation while keeping capability, planning and actual execution visibly separate.

## Resilience layers
1. Liveness: /api/health answers whether the API process is alive.
2. Readiness: /api/ready refuses real-AI readiness when ACE-Step is unavailable.
3. Durable state: SQLite preserves task state across API restarts in the current single-node deployment.
4. Recovery: interrupted processing/waiting tasks are re-queued after restart.
5. Bounded retry: provider failures use a bounded retry policy with provider-health records.
6. Container restart: Docker Compose uses restart: unless-stopped and health checks for API and ACE-Step.
7. Production HA: multiple GPU workers + durable queue + PostgreSQL/object storage are required for real multi-node 24/7 continuity.
8. Failover: a second independent GPU worker/provider is required if loss of one host must not interrupt service.

## Self-improvement contract
The system may collect metrics, detect repeated failures and propose upgrades. It must not silently rewrite and deploy production code.
Observe -> Diagnose -> Propose -> Test -> Review/Release -> Deploy -> Verify -> Roll back.
Signed releases or an explicit human-approved deployment gate remain required for production code changes.

## Public media modules
Music generation; story/film production planning; episodic continuity; podcast and live-broadcast adapter surfaces; news/game/cartoon production planning; product/offer campaign surfaces; creator/economic hub.

A module is LIVE only when a connected service and current runtime evidence support that claim. PLANNED, ADAPTER_REQUIRED, DEMO, OFFLINE and REVIEW_REQUIRED are first-class states.

## Scale boundary
A target audience of 850 crore can guide capacity planning, CDN strategy, moderation, localization and product architecture. It does not mean 850 crore concurrent users are supported. Capacity claims require measured load tests and deployed infrastructure.

## Acceptance tests
- API restart preserves queued tasks.
- Engine failure produces bounded retries and provider-health changes.
- /api/ready becomes unavailable when the engine is unavailable.
- Public UI never labels an unavailable engine as LIVE.
- Production code updates require a release gate.
- Live streaming is not claimed until a real streaming provider is connected.
