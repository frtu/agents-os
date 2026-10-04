# Clarifications & Known Deviations

Open questions, deferred decisions, and places where the code does not yet match
the specs. Feature specs mirror their `[NEEDS CLARIFICATION: …]` markers here.
Remove an entry when it is resolved (and note the resolution in the spec that
owns it).

---

## Known deviations (code lags spec)

| # | Principle / spec | Deviation | Tracked by |
| - | ---------------- | --------- | ---------- |
| KD-1 | [Constitution P4](./constitution.md#principle-4--engine-independence) · [workflow-engine](./workflow-engine/workflow-engine.md) | `backend/app/application/service.py` imports `SimulationEngine`, `ExecutionNotFound`, `HumanRequestNotFound` from `app.workflow.simulation`, and `build_control_center` imports `InProcessScheduler`, instead of depending on `workflow/port.py` only (the composition root belongs in `main.py`). | `backend/tests/test_constitution.py` (`KNOWN_ENGINE_IMPORTS`) |
| KD-2 | [api/rest-api.md](./api/rest-api.md) Status codes (`202` accepted for async execution) | `POST /stories/{id}/start` returns `200` with the Story Execution, not `202`. | `backend/tests/test_api_console_scenarios.py::test_story_execution_scenario_ac6` |

## Open questions

| # | Spec | Question | Status |
| - | ---- | -------- | ------ |
| — | — | — | — |
