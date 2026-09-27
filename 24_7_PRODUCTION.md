# Yatharth Music AI — 24/7 Production Architecture

## The important boundary

No software architecture can honestly guarantee that a service will never fail. The durable goal is automatic detection, safe recovery, durable state, and independent failover.

- detect failures automatically;
- do not silently lose requests;
- stop accepting real-AI work while the engine is unavailable;
- restart failed workers automatically;
- preserve task state and generated files across API restarts;
- alert when automatic recovery is exhausted;
- use a second compute provider when high availability is required.

## Current repository boundary

The FastAPI layer is separated from ACE-Step. The application exposes /api/health and /api/ready, Docker health checks are present, model/output volumes are persistent, and Colab plus Quick Tunnel are explicitly development/testing infrastructure.

ACE-Step exposes the asynchronous /release_task and /query_result API plus /health.

## Recommended production topology

```text
Internet
   |
HTTPS / CDN / reverse proxy
   |
Yatharth API replicas
   |
durable task queue + PostgreSQL
   |
GPU worker pool
   |---- GPU worker A: ACE-Step
   |---- GPU worker B: ACE-Step failover/capacity
   |
object storage
   |
audio delivery/CDN
```

### API layer

- Keep /api/health as liveness.
- Keep /api/ready as readiness.
- Never expose ACE-Step directly to the public internet.
- Keep ACESTEP_API_KEY server-side.
- Use exact CORS_ORIGINS in production.

### Durable task layer

The current in-memory tasks dictionary is appropriate for development and single-process testing, but it is not durable production state.

For production, move task records to PostgreSQL and queue work through Redis/RQ, Celery, or an equivalent durable queue. Persist task id, idempotency key, owner, request payload, state, retry count, engine task id, timestamps, final audio object key, and recovery history.

A worker restart must safely resume or requeue unfinished jobs.

### GPU worker layer

Run ACE-Step as a dedicated worker service.

The repository pins ACE-Step to a tested release in Docker Compose and forces the headless matplotlib backend to Agg. This prevents notebook UI matplotlib state from leaking into the server process.

Use restart policy, health probes, persistent model/cache/output volumes, and an external orchestrator when unhealthy-container replacement is required. Use at least two independent GPU workers when service continuity must survive loss of one GPU host.

A Docker healthcheck marks a container unhealthy; an orchestrator is responsible for replacing unhealthy workloads.

### Storage and delivery

Generated audio should not depend on a temporary notebook filesystem. Use object storage with lifecycle/versioning and store the object key in task state. This separates audio delivery from GPU lifetime.

### Observability

Monitor API availability, API readiness, ACE-Step health, queue depth, oldest queued job, generation latency, retries, GPU memory/utilization, disk space, and object-storage failures.

## Free-first path

The Colab notebook remains useful for development:

```text
Colab GPU -> ACE-Step -> local Yatharth API -> temporary tunnel
```

It cannot provide guaranteed 24/7 hosting because the notebook runtime and public tunnel are temporary infrastructure.

The only genuinely persistent zero-cost path is hardware you control and keep powered, with an NVIDIA GPU, Docker, restart policy, and monitoring. If the hardware, power, or network disappears, no software-only layer can keep the service online.

## Production migration sequence

1. Validate the Colab startup gate.
2. Validate local Docker GPU deployment.
3. Move task state from memory to PostgreSQL.
4. Add a durable queue such as Redis/RQ or Celery.
5. Move generated audio to object storage.
6. Put the API behind HTTPS and a reverse proxy/CDN.
7. Deploy one persistent GPU worker.
8. Add health monitoring and automatic replacement.
9. Add a second GPU worker/provider for failover.
10. Load-test worker restart, engine crash, API restart, storage failure, queue recovery, and duplicate submissions.

## Acceptance tests

- Kill ACE-Step and verify automatic recovery.
- Make ACE-Step unhealthy and verify orchestrator replacement.
- Kill the API and verify unfinished durable jobs remain recoverable.
- Remove one GPU worker and verify another worker can consume queued jobs.
- Repeat a network submission and verify idempotency prevents duplicate generation.
- Temporarily fail object storage and verify the task remains recoverable.
- Stop Colab and verify production is unaffected because production no longer depends on Colab.