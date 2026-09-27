# Production resilience

## What this solves

The free-Colab experiment can fail before ACE-Step starts when the notebook exports
Jupyter's `matplotlib_inline` backend. The resilient launcher forces the non-GUI
`Agg` backend and refuses to start the public API until ACE-Step answers its
health endpoint.

Run:

```bash
chmod +x scripts/launch_resilient.sh
ACE_ROOT=/content/ACE-Step-1.5 \
YATHARTH_ROOT=/content/yatharth-music-ai \
scripts/launch_resilient.sh
```

## What it does not promise

A Colab runtime is ephemeral. A temporary tunnel is also ephemeral. Neither is a
24/7 production host. Permanent availability requires a persistent GPU/compute
provider, persistent storage, monitoring, and an external process supervisor.

The repository already keeps generation state durable and retries failed engine
tasks. This launcher adds a deterministic startup gate so the application does
not advertise a real-AI service while the engine is unavailable.

## 24/7 target architecture

Use these layers:

1. Public HTTPS edge / CDN / WAF.
2. Stateless Yatharth API replicas.
3. Durable task database/queue.
4. GPU worker pool running ACE-Step.
5. Object storage for generated media.
6. Health checks + process restart.
7. Metrics/logging/alerting.
8. Signed, tested releases only for automatic upgrades.
9. Human approval before public-content publication.

Self-healing should retry/recover failed work; it should not silently rewrite or
self-upgrade production code. Upgrades must remain auditable and reversible.

## Public production features

The existing Studio API supports structured story, character, storyboard, music,
animation, editing and QC stages. Live streaming, live production, news, games,
cartoons, advertising, social publishing and an always-running episodic engine
should be implemented as separate provider adapters and queues rather than being
coupled to the music-generation process.

No external render, stream, publication, audience count, advertisement delivery,
or revenue result should be reported as complete until an actual provider returns
verifiable evidence.
