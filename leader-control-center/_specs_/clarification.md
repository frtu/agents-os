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
| KD-3 | [backend/storage.md](../backend/storage.md#target-design-decided-2026-10-18) D1 · constitution (history is permanent) | `SimulationEngine.start_story` / `retry` (`backend/app/workflow/simulation.py`) pop the previous `StoryExecution`; its timeline rows are orphaned and its Human Requests/Decisions reference a vanished execution. | — |
| KD-4 | storage.md D2 · [domain/event-model.md](./domain/event-model.md) | No persisted `event` table; bus messages are only fanned out to WebSockets with a global in-memory sequence. Timeline is written directly, not projected. | — |
| KD-5 | storage.md D3 · data-model (optimistic locking) | `Database.save` rewrites every row on each bus event and never checks `version`; Catalog and Runtime models carry no `version`. | — |
| KD-6 | storage.md D5 · data-model `artifact.location` | Artifact `content` is stored inline in the JSON document; no `location`/`metadata`. | — |
| KD-7 | storage.md D6 | `DELETE /workflow-definitions/{id}` and `DELETE /activity-definitions/{id}` hard-delete; referencing Stories/Schedules keep dangling ids. | — |
| KD-8 | storage.md D7, D8 | Ids are `prefix_` + 8 hex (`infra/store.py::uid`); Human Requests and Runtime documents persist denormalized display names. | — |
| KD-9 | storage.md D9 · data-model `epic` | `EpicRow` persists only `id, initiative_id, title`. | — |
| KD-10 | [database/api-storage-mapping.md](./database/api-storage-mapping.md) | Field-level gaps vs data-model (capability/provider missing `portfolio_id`/`status`/`version`; `provider.supported_capabilities` inverted onto capability; `capability_version`, `provider_execution.result` missing; `schedule.catch_up_window` ISO duration vs seconds; notification without `user_id`; decision `user` without FK). | Ossie model `LEADER_CONTROL_CENTER.mvp` notes |

## Open questions

| # | Spec | Question | Status |
| - | ---- | -------- | ------ |
| — | — | — | — |
