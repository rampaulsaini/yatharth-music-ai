# Yatharth Music AI — Production Control Plane

This document defines the durable boundary for a 24/7 service. It deliberately does **not** promise zero failure: real availability requires independent infrastructure, health detection, recovery, durable state, and failover.

## Control-plane objectives

- Liveness and readiness are separate.
- AI generation is never exposed directly to browsers.
- Every generation request has durable state and bounded retries.
- Provider health is observable.
- A failed provider does not silently become a successful generation.
- Automatic recovery is bounded and auditable.
- Software upgrades are signed/reviewed changes, not uncontrolled self-modification.
- Generated media is separated from temporary GPU files.
- Public media, live streaming, podcast, games, animation and advertising are adapter-driven capabilities; a UI card alone never claims a running backend.

## Required production topology

Internet → HTTPS/CDN/WAF → API replicas → durable queue → GPU worker pool → object storage/CDN.

Minimum high-availability target:

1. two API replicas;
2. durable PostgreSQL task state;
3. durable queue (Redis/RQ, Celery, or equivalent);
4. two independent GPU workers/providers;
5. versioned object storage;
6. external monitoring and alerting;
7. automated unhealthy-worker replacement;
8. backup and restore tests.

## Self-healing contract

Automatic actions may:

- retry transient provider failures with exponential backoff;
- requeue recoverable work after process restart;
- stop accepting AI work when readiness is false;
- route work to a healthy secondary provider;
- restart an unhealthy worker through the deployment orchestrator;
- preserve failed tasks for inspection.

Automatic actions must not:

- invent successful output;
- mark unverified media as VERIFIED;
- expose secrets;
- silently change application code;
- bypass human/legal publication gates.

## Self-upgrade contract

"Self-upgrading" means an agent may observe telemetry, propose a change, run deterministic tests, and prepare a signed/reviewed release. Production deployment remains gated by the release policy. This prevents an autonomous loop from modifying its own safety boundary.

## Public media capability map

The public interface may expose these modules:

- AI Music Studio
- Creative Story/Film Studio
- Live Podcast
- Live Streaming
- Live Production
- Live News
- Live Games
- Animation/Cartoon
- Creator/Economic Hub
- Product offers and advertising
- Social distribution
- Endless episodic storytelling

Each module requires an explicit backend adapter, rights/licensing policy, moderation controls, observability, and a publication state. "Planned", "ready", "live", and "verified" are distinct states.

## Advertising and offers

Advertising should be first-party/consented and configurable. The system may schedule product cards, offers and campaign variants, but it must not fabricate availability, prices, endorsements, audience numbers, or performance metrics. Social posting requires platform-specific credentials and policy compliance.

## 24/7 acceptance tests

Before calling the service production-ready, continuously test:

- API restart during generation;
- GPU worker crash;
- provider health loss and recovery;
- queue recovery;
- duplicate/idempotent submissions;
- object-storage outage;
- database restore;
- one-provider loss with another provider available;
- stale public status;
- unauthorized task/audio access;
- secret leakage scans;
- signed release verification.

## Current free-testing boundary

Google Colab + Quick Tunnel is a development/test path only. Its GPU runtime and public URL are temporary. The repository's notebook now sets a headless matplotlib backend before ACE-Step startup and waits for the engine health endpoint before exposing the test URL. Permanent availability requires persistent infrastructure.
