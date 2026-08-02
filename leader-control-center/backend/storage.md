# Backend Storage Spec — SQLite (MVP)

Backend-local **overlay** on the canonical storage specs. It does not restate the
schema; it declares the persistence technology for this backend and records the
exact deltas from the Postgres-oriented data model.

Canonical sources (read first, they remain authoritative for entities, fields,
relationships, and invariants):

- Schema & relationships: [`../_specs_/database/data-model.md`](../_specs_/database/data-model.md)
- Tech stack & layering: [`../_specs_/backend/architecture.md`](../_specs_/backend/architecture.md)
- Topology: [`../_specs_/deployment/deployment.md`](../_specs_/deployment/deployment.md)

Where this file and the canonical specs disagree **on storage technology only**,
this file wins for the backend. For everything else (entities, fields,
relationships, state machines, invariants), the canonical specs win.

---

## Decision

Use **SQLite** as the backend datastore for the MVP — a single embedded,
file-based database. No server, no docker-compose Postgres, no separate event
store; the event log and all projections live in the same SQLite file.

### Location

The database file lives in the **project-root `data/` directory**, i.e.
`../data/` relative to `backend/`:

```text
leader-control-center/
  data/                         # SQLite file(s) live here (gitignored)
    leader-control-center.db
  backend/                      # cwd when running uvicorn
```

- Default path: `../data/leader-control-center.db` (resolved from the backend
  working directory).
- Configurable via `SQLITE_PATH` (see README config table).
- The backend creates the `data/` directory on startup if it is missing.
- `data/` is gitignored — the database is local state, not source.

---

## Patches vs. the canonical data model

The canonical schema in [`../_specs_/database/data-model.md`](../_specs_/database/data-model.md)
targets PostgreSQL. Apply these substitutions when realizing it on SQLite. Entity
set, columns, relationships, and immutability rules are unchanged.

| Canonical (Postgres) | SQLite realization | Notes |
| -------------------- | ------------------ | ----- |
| `PostgreSQL` server | Embedded SQLite file at `../data/` | Single file; no network service. |
| `uuid` id columns | `TEXT` (UUID/string ids) | Matches the app's string ids (e.g. `story_ab12cd34`). |
| `jsonb` columns (`inputs`, `outputs`, `config`, `options`, `metadata`, `payload`, `success_criteria`, `default_ai_config`, `result`, `input` (workflow_definition JSON Schema), `template_input`) | `TEXT` holding JSON | Query with SQLite's `json1` functions (`json_extract`, etc.). |
| `uuid[]` arrays (`provider.supported_capabilities`) | `TEXT` JSON array, **or** a junction table `provider_capability(provider_id, capability_id)` | Prefer the junction table if you need to query/join by capability. |
| `timestamptz` (`created_at`, `updated_at`, `started_at`, …) | `TEXT` ISO-8601 UTC (`…Z`) | Same wire format the app already emits; string-sortable. |
| `version` (optimistic locking) | `INTEGER` | Semantics unchanged: bump on write, guard with `WHERE version = ?`. |
| `event.sequence` (monotonic per aggregate) | `INTEGER` | Enforce monotonicity in application code / a per-aggregate counter. |
| Separate Transaction Store + Event Store (polyglot) | One SQLite file | Polyglot persistence collapses to a single file for the MVP; the repository seam is preserved so it can split later. |
| docker-compose Postgres service | none | Nothing to provision; the file is created on first run. |

Unchanged from the canonical spec: every mutable row keeps `id`, `created_at`,
`updated_at`, `version`; `event`, `decision`, and `artifact` rows are immutable;
Planning has no FK to Runtime; `dependency` forms a DAG within a Story.

---

## Fit with the architecture

SQLite sits behind the existing repository / event-bus seam (`app/infra/`), the
same seam the in-memory MVP store uses today (`app/infra/store.py`). Swapping
in-memory → SQLite, or SQLite → Postgres later, is an `infra/` change only;
`application/` and `domain/` are untouched. This keeps the
[architecture](../_specs_/backend/architecture.md) invariant intact:
`api → application → domain`, adapters depend on domain ports.

---

## MVP implementation (as built)

The MVP realizes storage as **aggregate persistence**, not the normalized schema
above — that (per-entity tables, FKs, event log) is deferred.

- **Working set + write-through.** The `Store`'s in-memory dicts remain the
  runtime working set. `app/infra/db.py` (`Database`) is the durable seam: on
  boot it loads persisted state (or the app seeds and saves on first run); every
  state change signalled on the domain **event bus** flushes the store to SQLite.
  Because the bus already fires on every mutation, `application/`, `domain/`, and
  `workflow/` need no changes.
- **One table, JSON documents.** All aggregates persist to a single table
  `aggregates(collection, id, ord, data)`, where `data` is the aggregate
  serialized as JSON (Pydantic `model_dump_json`). Deep runtime aggregates
  (`StoryExecution → TaskExecution → CapabilityExecution → ProviderExecution`)
  are stored as one document per story execution. `ord` preserves list order for
  timelines, artifacts, and notifications. Derived indexes (e.g.
  `execution_by_story`) are rebuilt from the loaded aggregates.
- **Writes** are full-snapshot rewrites in a single transaction (guarded by a
  lock, since the simulation tick and request handlers can both trigger a save).
  Fine at MVP scale; splitting into per-aggregate writes or the normalized schema
  is a later `infra/` change.
- **Location & config.** File at `SQLITE_PATH` (default
  `../data/leader-control-center.db`); the `data/` directory is created on
  startup. Tests set `SQLITE_PATH=:memory:` for a fresh seed per app.
