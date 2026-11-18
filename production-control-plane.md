# Yatharth Omniverse Production Control Plane

## Goal
Provide a provider-neutral control plane for continuous creative production without pretending that a free notebook can provide guaranteed 24/7 uptime.

## Reliability layers
1. **Liveness** — process is reachable.
2. **Readiness** — required AI provider is reachable.
3. **Durable state** — SQLite WAL persists tasks across process restarts.
4. **Recovery** — interrupted tasks return to the queue.
5. **Retry/backoff** — transient provider failures are retried with bounded attempts.
6. **Degraded mode** — planning, catalog, live schedule and existing media remain usable when GPU generation is unavailable.
7. **Supervisor** — production deployment restarts failed workers and records restart events.
8. **Observability** — health, readiness and resilience endpoints are monitored.
9. **Safe upgrades** — updates are allow-listed/signed or human-approved; the runtime never rewrites its own source.
10. **Human gate** — publication, monetization and claims of verification remain reviewable.

## Continuous-service topology

Browser/PWA → CDN/WAF → API → durable queue → CPU orchestration workers → GPU music/video workers → object storage/CDN.

At least two independent GPU workers should be available for production. A worker failure must drain/requeue work rather than take the public interface offline.

## Live media
The command center supports:
- live studio schedule
- podcast/live show slots
- stream embeds and player surfaces
- news/editorial feed
- game/cartoon channels
- creator episodes
- product/ad inventory

External streams are integrations, not generated claims. Each source should carry an explicit source URL and status.

## Monetization
Ads are represented as inventory slots and campaign metadata. Social platforms require their own approved APIs/accounts and cannot be assumed to publish automatically. Every campaign should have frequency, destination, budget and approval state.

## Never-fail principle
No software system can honestly guarantee zero failures. The engineering target is **no single failure taking down the whole service**, automatic recovery where safe, durable queues, and visible degraded operation when dependencies are unavailable.
