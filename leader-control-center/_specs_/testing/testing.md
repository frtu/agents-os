# Testing & Acceptance

Verification is anchored to the [constitution](../constitution.md) invariants
and to each spec's Acceptance Criteria. Every invariant maps to at least one
automated test; every feature AC maps to the test that proves it (see the
feature's `plan.md` → Test Plan).

```bash
cd backend && uv run --extra dev pytest        # backend suite (offline, deterministic)
cd frontend && npm run typecheck && npm run build   # frontend contract + build gate
```

---

## 1. Invariant Test Matrix

| Invariant | Principle | Test focus | Test |
| --------- | --------- | ---------- | ---- |
| camelCase on the wire + resource envelope | P6 | responses carry `id · version · createdAt · updatedAt`, camelCase keys | `test_smoke.py::test_initiatives_summary_shape` |
| Problem+JSON errors | P6, P9 | unknown id → 404 Problem+JSON with a meaningful `detail` | `test_smoke.py::test_unknown_execution_returns_problem_json` |
| Engine concepts stay in `workflow/` | P4 | no `temporalio` import outside `app/workflow/`; application imports only the ports | `test_constitution.py::test_engine_concepts_stay_in_workflow_p4` · `::test_business_code_depends_on_ports_only_p4` |
| Thin routers | P3 | `app/api/` never imports `infra/` or `workflow/` | `test_constitution.py::test_routers_only_reach_the_application_layer_p3` |
| Every resource model is camelCase | P6 | every `domain/models.py` model inherits the camelCase base | `test_constitution.py::test_domain_models_serialize_camel_case_p6` |
| Planning never mutated by runtime | P2 | a scheduled occurrence creates a *new* Story; Completed Stories are not re-opened | `test_schedules.py::test_occurrence_creates_and_starts_a_story` |
| Referential integrity of catalog | P2 | deleting a referenced Workflow Definition → 409 | `test_smoke.py::test_delete_referenced_workflow_definition_conflicts` |
| Invariant violations are 422 | P6, P9 | templated Story without valid `templateInput` → 422 | `test_smoke.py::test_create_templated_story_requires_input` |
| Every pause is a Human Request | P1 | open Human Requests appear in the Attention Queue | `test_smoke.py::test_attention_and_notifications` |
| Rules run identically on every adapter | P4, P8 | firing algorithm with injected clock + in-process adapter, no Temporal | `test_schedules.py` (overlap, catch-up, auto-pause) |
| Failures carry their reason | P9 | invalid template pauses a Schedule with a recorded reason | `test_schedules.py::test_invalid_template_pauses_schedule` |
| Realtime never leaks engine ids | P4 | WS payloads carry no WorkflowId/RunId | *gap — add with the next realtime change* |
| Timeline append-only | P2 | existing timeline entries are never edited | *gap — add with the next timeline change* |

A *gap* row is an invariant without a test yet. The next change that touches
that area MUST close it.

## 2. Test Levels

- **Unit** — domain math and pure functions (schedule specs, template
  encoding, validators). No app, no DB.
- **Application** — `ControlCenter` / services against an in-memory store with
  an injected clock and a fake or in-process port. This is where business rules
  are proven.
- **API** — `TestClient(create_app())` over the real ASGI app, asserting the wire
  contract (status codes, camelCase, Problem+JSON) per
  [api/rest-api.md](../api/rest-api.md).
- **Architecture** — static checks of the layer boundaries
  (`test_constitution.py`).
- **Integration (opt-in)** — against the local Temporal stack
  (`../start.sh`, `scripts/temporal-api.sh`). Never required for the default
  suite.
- **Frontend** — `npm run typecheck` is the contract gate for
  `types/domain.ts`; `npm run build` must pass.

## 3. Conventions

- **One test module per feature or area spec** (`test_<feature>.py`), with a
  module docstring naming the spec it covers.
- **Traceability:** a test that proves an FR/AC cites it in a comment
  (`# spec 002 AC-3`) and ends its name with the id (`test_…_ac3`).
  Invariant tests end with the principle (`test_…_p4`).
- **Deterministic:** `conftest.py` forces `SQLITE_PATH=:memory:`; time comes from
  an injected clock; no network, no Temporal, no sleeps.
- **Isolation:** each test builds its own app / `ControlCenter`; no ordering
  dependencies between tests.

## 4. Acceptance Gate

A change is acceptable when: the backend suite passes; the frontend typecheck
and build pass; every AC of the touched feature has a mapped, passing test; no
new *gap* row was introduced; and spec, code, and tests agree.

## 5. Acceptance Criteria

- AC-1: Each constitution invariant has ≥1 automated test or an explicit *gap*
  row with an owner change.
- AC-2: Every feature `plan.md` has a Test Plan mapping each AC to a test.
- AC-3: The default suite runs offline with no external dependency.
- AC-4: Layer boundaries (P3, P4) are enforced by a static test; known
  deviations are listed in [clarification.md](../clarification.md) and in the
  test's allow-list, never silently.
