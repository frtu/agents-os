# Feature Specs

Feature folders are the **buildable layer** of the spec-kit (GitHub Spec-Kit
standard: constitution → spec → plan → tasks). Each feature refines the area
specs (`overview/`, `domain/`, `planning/`, `execution/`, `api/`, …) it touches;
where a feature and an area spec disagree, the **later feature wins** and the
area spec carries an in-place amendment note pointing to the feature.

```text
_specs_/features/
└── NNN-short-name/
    ├── spec.md    # what & why — FR-N, User Scenarios, AC-N   (from _templates/spec-template.md)
    ├── plan.md    # how — Constitution Check, contracts, test plan (from _templates/plan-template.md)
    └── tasks.md   # ordered build steps tied to FR/AC          (from _templates/tasks-template.md)
```

## Rules

- **Numbering:** three digits, monotonically increasing, never reused
  (`001-…`, `002-…`). The short name is kebab-case.
- **Scope decides the files:** a small behavioural fix may need only `spec.md`;
  anything spanning backend + frontend or adding endpoints gets all three.
- **Ids are stable:** FR/AC numbers are never renumbered. A dropped requirement
  is marked `~~FR-4~~ (removed YYYY-MM-DD: reason)`; an amendment appends new ids
  (FR-15, AC-9…) with a dated note.
- **Citations:** code comments cite `spec NNN FR-N`; tests cite `spec NNN AC-N`
  in a comment and end their name with the id (`test_…_ac3`). Area-spec
  requirements are cited by path (`spec planning/schedules D4`).
- **Amends:** every area spec the feature changes is listed at the top of
  `spec.md`, and updated in the same change.

## Index

| Feature | Status | Summary |
| ------- | ------ | ------- |
| [001-api-console](./001-api-console/spec.md) | Draft | Developer API Console: endpoint explorer, scenarios, realtime log. |
| [002-backend-console](./002-backend-console/spec.md) | Draft | Read-only Gradio console at `/ui`: Board, Definitions, Executions. |

## Before this model (area specs only)

These capabilities were specified directly in area specs, before feature folders
existed. They stay authoritative there; new changes to them start a feature
folder that amends the area spec.

| Capability | Spec | Tests |
| ---------- | ---- | ----- |
| Schedules (time-triggered Stories) | [planning/schedules.md](../planning/schedules.md) | `backend/tests/test_schedules.py` |
| Activity Definitions (UI "Tasks") | [execution/activity-definitions.md](../execution/activity-definitions.md) | `backend/tests/test_activity_definitions.py` |
| Planning / board / decisions / catalog MVP | [api/rest-api.md](../api/rest-api.md) | `backend/tests/test_smoke.py` |
