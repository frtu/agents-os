# API ↔ Storage Mapping

Maps the as-built REST/WS surface (`backend/app/api/routers/`) and its SQLite
realization ([`backend/storage.md`](../../backend/storage.md),
`backend/app/infra/db.py`) onto the canonical schema in
[data-model.md](./data-model.md). The same mapping is machine-readable in the
Apache Ossie model [`ossie/leader-control-center.ossie.yaml`](./ossie/leader-control-center.ossie.yaml)
(vendor extension `LEADER_CONTROL_CENTER` → `mvp`, `api`).

Physical MVP: one table `aggregates(collection, id, ord, data JSON)`, full-snapshot
rewrite on every bus event. "Path" is the JSON path inside `data`.

Status as of 2026-10-18.

---

## Entity map

| Canonical table | MVP collection · path | API surface | Gaps vs canonical |
| --- | --- | --- | --- |
| `workspace` | — | — | Not implemented. |
| `portfolio` | — | — | Not implemented; children carry constant `portfolio_default`. |
| `capability` | `capabilities` · `$` | `GET /capabilities` | No `portfolio_id`, `version`, `status`, audit cols; `inputs`/`outputs` are text, not JSON; holds `supported_providers` (inverse direction). |
| `provider` | `providers` · `$` | `GET /providers` | No `portfolio_id`, `config`, `credential_ref`, `status`, audit cols; `supported_capabilities` lives on capability. |
| `provider_capability` *(proposed)* | derivable from `capabilities.$.supported_providers[*]` | — | storage.md alternative to `uuid[]`. |
| `workflow_definition` | `workflow_definitions` · `$` | CRUD `/workflow-definitions` | **Hard delete**: stories/schedules keep a dangling id. |
| `activity_definition` | `activity_definitions` · `$` | CRUD + `/render`, `/test` | Hard delete. |
| `initiative` | `initiatives` · `$` | `/initiatives` (+ `reorder`, `delete`, `board`) | Extra `order`; extra status `Deleted` (soft delete, stories reparented to `init_misc`). |
| `epic` | `epics` · `$` (thin `EpicRow`) | none | Only `id, initiative_id, title`; exactly one implicit epic per initiative. |
| `story` | `stories` · `$` | `/stories` (+ `draft`, `tasks`, `artifacts`, `start`) | Extra status `Deleted`; acceptance criteria embedded. |
| `acceptance_criteria` | `stories` · `$.acceptance_criteria[*]` | via story | Story-level only (no `task_id`). |
| `task` | `tasks` · `$` | `/stories/{id}/tasks`, `/tasks/{id}/ready|start` | No `capability_version`; dependencies embedded. |
| `dependency` | `tasks` · `$.dependencies[*]` | via task | DAG not enforced by storage. |
| `schedule` | `schedules` · `$` | `/schedules` (+ pause/resume/trigger/archive/preview) | `catch_up_window` ISO-8601 duration vs `catch_up_window_seconds`. |
| `schedule_run` | `schedule_runs` · `$` | `/schedules/{id}/runs` | Extra `settled_at`, `outcome`; `unique(schedule_id, scheduled_for)` in code only. |
| `story_execution` | `story_executions` · `$` | `/stories/{id}/start`, `/executions/{id}` (+ cancel/retry) | No audit/`version`; extra `progress`. **Start/retry pop the previous execution** — one run per story survives. |
| `task_execution` | `story_executions` · `$.task_executions[*]` | nested | Extra `task_name`, `attempt`, `waiting_reason`. |
| `capability_execution` | `…task_executions[*].capability_executions[*]` | nested | Extra `capability_name`. |
| `provider_execution` | `…capability_executions[*].provider_executions[*]` | nested | Extra `provider_name`; no `result`. |
| `human_request` | `human_requests` · `$` | `GET /attention`, `/executions/{id}/decisions` | Denormalized `story_id`, `story_title`, `initiative_title`, `actions`. `execution_id` = story execution (canonical leaves it ambiguous). |
| `decision` | `decisions` · `$` | `/executions/{id}/decisions/history`, `…/{rid}/{approve…custom}` | `user` free text (no `user_id` FK); extra `action_name`. |
| `artifact` | `artifacts` · `$` (`ord`) | `/stories/{id}/artifacts`, `/artifacts/{id}` | Content **inline**; no `owner`, `location`, `metadata`; extra `story_id`, `name`, `language`. |
| `event` | — | `WS /stream` | **Not persisted.** Bus sequence is global and in-memory, not per aggregate. |
| `timeline_entry` | `timeline` · `$` (`ord`) | `/executions/{id}/timeline` | Written directly, not projected from events; `category`+`detail` vs `payload`. |
| `attention_item` | derived on read from `human_requests` | `GET /attention` | Not materialized (fine at MVP scale). |
| `board_view` | derived on read | `/initiatives/{id}/board`, `GET /initiatives` | Not materialized. |
| `notification` | `notifications` · `$` (`ord`) | `/notifications` (+ open/ack/close) | No `user_id`; `status` enum vs `read` bool; `message` vs `payload`. |
| `app_user`, `credential` | — | — | Not implemented. |

## Cross-cutting observations

1. **History is not permanent at runtime.** Restart/retry deletes the prior
   `StoryExecution` aggregate; its timeline rows stay orphaned and its Human
   Requests/Decisions point at a vanished execution (constitution: history is
   permanent; data-model: runtime is disposable — the two need reconciling).
2. **No event store.** data-model says the `event` table is authoritative and
   projections are rebuildable; the MVP persists projections directly.
3. **Optimistic locking is nominal.** `version` exists on Resources, but the
   snapshot rewrite never checks it, and runtime/catalog models have none.
4. **Referential integrity is application-only** (JSON documents, no FKs), and
   hard deletes on catalog entries can strand Planning references.
5. **Ids are `prefix_` + 8 hex (32 bits)** vs canonical `uuid`; collision odds
   reach ~1% around 9k ids per prefix.
6. **Write amplification.** Every bus event rewrites the whole DB; timelines and
   artifact content grow it unboundedly.
