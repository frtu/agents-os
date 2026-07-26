# Deployment

> MVP-depth spec.

Deployment topology for a single-Portfolio MVP. The design keeps the API
available even when the workflow engine is degraded (Availability NFR).

---

## Components

```
┌────────────┐     ┌──────────────┐     ┌──────────────┐
│  Frontend  │────▶│  Backend API │────▶│  PostgreSQL  │
│  (React)   │◀────│  (FastAPI)   │     └──────────────┘
└────────────┘  ws └──────┬───────┘
                          │ port/adapter
                   ┌──────▼───────┐
                   │   Temporal   │
                   │  (+ workers) │
                   └──────────────┘
```

- **Frontend:** static build served via CDN/host.
- **Backend API:** FastAPI app (REST + WebSocket).
- **Workers:** Temporal workflow/activity workers (may be separate processes).
- **PostgreSQL:** planning, runtime, events, projections.
- **Temporal:** durable execution engine.

---

## Environments

- Local: docker-compose (API, Postgres, Temporal, workers).
- Staging/Prod: containerized services; Temporal managed or self-hosted.

---

## Configuration

- Secrets (provider credentials, DB, Temporal) via environment/secret manager;
  never in code or the event log.
- Provider config and the Capability Catalog are data, not deployment artifacts.

---

## Resilience

- API and workers scale independently.
- If Temporal is unreachable: reads (board, timeline, artifacts) keep working;
  execution commands return `503` with a retriable error. See
  [../observability/observability.md](../observability/observability.md).
- Projections are rebuildable from the event log after recovery.

---

## Future

- Multi-Portfolio isolation
- Horizontal scaling of workers per task queue
- Blue/green or rolling deploys with schema migrations
- Additional workflow-engine deployments via adapters
