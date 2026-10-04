# Implementation Plan: [FEATURE NAME]

**Feature ID:** `NNN-short-name` · **Spec:** [`spec.md`](spec.md)
**Status:** Draft | In Review | Approved
**Created:** YYYY-MM-DD · **Last Updated:** YYYY-MM-DD

> Describes **how**. Turns the spec into an architecture and technical approach.
> Do not restate requirements — reference them (FR-1, AC-2). Record open
> technical choices under **Open Technical Choices**, not as silent decisions.

## Constitution Check

Confirm alignment with each principle in [`constitution.md`](../../constitution.md).
Note and justify any deviation.

- [ ] P1 Human first; every pause is a Human Request (one Decision each)
- [ ] P2 Planning immutable · Runtime disposable · History permanent
- [ ] P3 Business first; command-oriented surfaces; thin routers
- [ ] P4 Engine independence (engine concepts stay in `workflow/`)
- [ ] P5 Provider independence (Capability / Strategy / Provider)
- [ ] P6 Contract lockstep (`models.py` ↔ `domain.ts` ↔ `api/*.md`, camelCase)
- [ ] P7 Spec first (FR/AC ids cited in code and tests)
- [ ] P8 Tested or not done (offline, deterministic, injected clock / fake port)
- [ ] P9 Error transparency
- [ ] P10 Progressive automation, simplest thing first
- [ ] P11 Ubiquitous language

## Technical Context

- **Backend:** FastAPI · Pydantic v2 · SQLite write-through · `workflow/port.py`
- **Frontend:** React · TanStack Query · Zustand · shadcn-style primitives
- **Dependencies on other features / area specs:** …

## Architecture Overview

How the pieces fit, layer by layer:

```text
api/routers → application (ControlCenter / services) → domain
                         ↘ workflow/port.py → adapter (simulation | temporal)
infra (store, event bus, SQLite)   ·   frontend (api client → hooks → features)
```

## Components

Per layer: responsibility, inputs/outputs, files touched.

- **domain/** — models, enums (camelCase on the wire).
- **application/** — commands / queries / process managers.
- **workflow/** — port changes; adapter changes.
- **infra/** — store, SQLite schema, seed.
- **api/** — routes (thin), schemas, errors, realtime messages.
- **frontend/** — `types/domain.ts`, `api/` (http + mock), hooks, `features/`.

## Data Contracts

Wire shapes (camelCase JSON), SQLite tables/columns, realtime message types.
Reference [`database/data-model.md`](../../database/data-model.md) rather than
duplicating it.

## Interfaces / Contracts

| Method | Path | Body | Returns | FR |
| ------ | ---- | ---- | ------- | -- |
| `POST` | `/api/v1/…` | `{…}` | `…` | FR-1 |

Commands → events emitted. Error cases → status code + Problem+JSON `type`.

## Test Plan

Map each AC to the test that proves it (file + test name). Tests run offline.

| AC | Test |
| -- | ---- |
| AC-1 | `backend/tests/test_<feature>.py::test_…_ac1` |

## Alternatives Considered

Options weighed and why they lost.

## Open Technical Choices

Undecided options (mirror into [`clarification.md`](../../clarification.md)).

## Risks & Mitigations

- Risk → mitigation.

## Rollout / Sequencing

Incremental delivery; what an MVP slice looks like.
