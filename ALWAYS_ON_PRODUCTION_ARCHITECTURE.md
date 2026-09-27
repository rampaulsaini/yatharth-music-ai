# Yatharth Always-On Production Architecture

## Objective

Provider-neutral, fail-closed production architecture for Yatharth Music AI and future live/media services.

### Availability contract

- Colab and temporary tunnels are development/test environments only.
- Production requires persistent compute, durable storage, an external queue, health monitoring, and restart supervision.
- No component advertises `AI ENGINE READY` unless the engine health endpoint is reachable.
- Recovery may restart services and replay idempotent work, but must not silently rewrite application code or publish unreviewed content.

## Multi-layer control plane

1. Public HTTPS edge — CDN/WAF, rate limits and authentication.
2. Stateless API replicas behind the edge.
3. Durable queue with task IDs and idempotency keys.
4. Replaceable GPU workers running ACE-Step or another provider adapter.
5. Object storage for generated media.
6. Durable database for tasks, creators, products, campaigns and publication metadata.
7. Supervisor for health checks, restart, backoff, dead-letter handling and alerting.
8. Metrics, structured logs, traces and synthetic generation tests.
9. Release gates for syntax, unit, integration, security and smoke tests.
10. Human verification boundaries for substantive public claims and sensitive publication.

## Self-healing

Use deterministic recovery: restart unhealthy workers; exponential backoff; preserve task state before retry; idempotency keys; dead-letter exhausted tasks; expose degraded mode; alert when recovery budgets are exhausted.

## Self-upgrading

Do not mutate production code in place. Use `observe -> test candidate -> build immutable artifact -> smoke test -> canary -> promote -> monitor -> rollback`. Record software/model version, configuration hash and test evidence for every promotion.

## Live media expansion

Keep music generation independent from future adapters for live podcast, live streaming, live production, news presentation, games, animation/cartoon production, episodic stories, social publishing, and digital-store campaigns. Each adapter needs its own queue, credentials, health contract, retry policy and evidence record so one failure cannot take down music generation.

## Always-running episodic engine

Represent an infinite series as bounded, recoverable episodes. Each episode has an immutable ID, previous-episode reference, world/character state, script, assets, QC, publication state and provenance. Completion schedules the next episode; failure isolates only that episode.

## Advertising and economic layer

Treat ads/offers as campaign objects. Track configured, generated, scheduled, provider-accepted, delivered and verified-conversion states separately. Never infer audience, delivery or revenue merely because automation created a campaign.

## Scale

A target audience is capacity-planning input, not evidence of actual audience size. Measure concurrency, requests/sec, queue depth, GPU throughput, storage growth and observed error rates.

## Reliability target

No distributed system can honestly guarantee that it will never fail. The engineering target is: **detect -> isolate -> recover -> verify -> resume**, with no silent data loss and no false healthy state.

## Production readiness gate

- [ ] Persistent GPU provider selected
- [ ] Durable database and queue deployed
- [ ] Object storage and backups deployed
- [ ] Secrets kept outside source code
- [ ] Multi-instance API tested
- [ ] GPU restart and queue replay/idempotency tested
- [ ] Dead-letter recovery tested
- [ ] Synthetic generation and alerting tested
- [ ] Rollback tested
- [ ] Live-media adapters isolated
- [ ] Public-content verification boundary preserved
