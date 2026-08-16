# Tasks: Leader Assistant

**Feature ID:** `001-leader-assistant` · **Plan:** [`plan.md`](plan.md)
**Last Updated:** 2026-08-16

> Ordered build steps derived from the local spec set and [`plan.md`](plan.md). Each references the spec doc / invariant it satisfies. `[P]` = parallelizable (no shared files, no dependency). Remote's disposable `/api/...` URL tasks are intentionally **excluded** — endpoint paths are settled at build time per [`plan-tbd.md`](plan-tbd.md) (TBD-10).

## Legend
- `[ ]` pending · `[x]` done · `[P]` parallelizable
- Invariant refs point at [`20-testing`](../20-testing.md); spec refs use `[[NN-name]]`.

## Setup

- [ ] T001 Python 3.11+ project scaffold; pin `claude-agent-sdk`, `fastapi`, `gradio`, `uvicorn`. ([[19-non-functional]])
- [ ] T002 Config module: `LEADER_VAULT_ROOT` / `LEADER_VAULT_PATH` / `LEADER_DEFAULT_VAULT`. (P13, [[03-vault]])
- [ ] T003 [P] Wire `memory/constitution.md` + numbered specs into the agent system-prompt assembly.

## Core — Vault & git (foundation)

- [ ] T010 `vault` resolver: `Vaults/<name>/` layout scaffolding (`raw/{clippings,docs,notes,transcripts,assets}`, `wiki/…`, `sessions/`, `output/`); default + selector resolution. (P1, P13; [[03-vault]])
- [ ] T011 `raw/` write-guard: reject any write path under `raw/`. (P2; invariant "raw never rewritten"; [[18-security]])
- [ ] T012 Git/vault manager: typed commit messages (ingest|update|lint|synthesis|dreaming|spec|output), append-only `log.md`, portal writer. (P6; invariants "mutations→commits", "log append-only"; [[11-git-workflow]], [[17-observability]])
- [ ] T013 [P] Schema helpers: read/write/validate frontmatter, stable time-based `id`, slugify, `[[wikilink]]` + table-pipe escaping. (P4; [[02-domain-model]])

## Core — Knowledge pipeline

- [ ] T020 Ingestion orchestrator: raw → source-summary (`wiki/sources/{provenance}/`) → concept create/update → portal/log; invoke risk + git. (P3; [[04-knowledge-ingestion]])
- [ ] T021 Source classifier: `raw/` subfolder primary signal + content sniff; log the decision. ([[04-knowledge-ingestion]])
- [ ] T022 Dreaming operation: `sessions/` → `wiki/sources/_daily_/YYYY-MM-DD.md` (decisions, knowledge candidates). (P3; [[06-conversations]])
- [ ] T023 Zettelkasten manager: atomicity + justified link-context enforcement; dedup pre-check. (P4; invariants "atomicity", "wikilinks"; [[05-zettelkasten]])

## Core — Lifecycle (maturity: reference + counter)

- [ ] T030 `lifecycle` engine (pure fns): `compute_status`, `record_usage(concept, output_link)` → append `referenced-to` + increment `usage-count`, `record_big_correction` → set `last-correction`, demote `reliable→used`. (P5; [[05-zettelkasten]])
- [ ] T031 [P] Enforce single-writer rule: only `lifecycle` mutates `usage-count`/`referenced-to`/`last-correction`. (P5/P6)

## Core — Governance

- [ ] T040 Risk engine: load rules-as-data; evaluate (scope, condition, severity, action); highest-severity wins; audit to log. (P12; [[10-risk-engine]])
- [ ] T041 Branch policy: safe→`main`, risky→`feature/{name}`, no silent merge. (P12; invariant "risky→feature branch"; [[11-git-workflow]])
- [ ] T042 Planning engine: plan-first for consequential work; clarification only on material ambiguity. (P8; invariant "plan-first"; [[09-planning]])

## Core — Specifications

- [ ] T050 Specification engine: continuous generation from knowledge changes (impact analysis → draft/update → link → consistency check → risk → commit). (P11; [[07-specification-model]])
- [ ] T051 Spec semantic lifecycle `draft→review→approved`; approved-spec protection (edits become new revision, `MODIFY_APPROVED_SPEC`). (P11; invariant "approved not overwritten"; [[08-specification-lifecycle]])

## Core — Outputs (secondary) & templates

- [ ] T060 Output engine: reuse-before-create against root `templates/`; propose new template on no-match; write `output/` with citations. (P7; [[21-outputs]])
- [ ] T061 On production, call `lifecycle.record_usage` for each cited concept; append `output` log entry. (P6; [[21-outputs]])

## Interfaces (capability parity)

- [ ] T070 Surface-agnostic `capabilities` module: `list_vaults`, `create_vault`, `ingest`, `dream`, `query`, `plan`, `execute`, `produce`, `ask`, `lint`, `spec_read`, `spec_transition`. (P9; [[12-assistant]])
- [ ] T071 `ask()` over `claude-agent-sdk` with vault-scoped tools + resumable session + streaming. ([[14-chat]])
- [ ] T072 REST surface (FastAPI) over `capabilities`; SSE for streaming. Paths per TBD-10. (P9; [[13-api]])
- [ ] T073 Chat surface (Gradio on same app): vault picker, streaming, inline HITL confirmation. (P8/P9; [[14-chat]])
- [ ] T074 HITL bridge across transports (propose/confirm or `auto_approve`) — per TBD-2. (P8)

## Observability

- [ ] T080 Portal writer: one line per page, grouped by category, updated every ingest. (invariant "portal updated"; [[17-observability]])
- [ ] T081 Lint operation: contradictions, stale claims, orphans, missing coverage/cross-refs, misplaced pages; report then offer fixes; cadence per spec. ([[05-zettelkasten]], [[17-observability]])

## Validation (map to invariants & acceptance criteria)

- [ ] T090 Unit: risk predicates, frontmatter/ID validation, wikilink formatting, lifecycle math (incl. demotion). ([[20-testing]])
- [ ] T091 Integration: ingest pipeline; dreaming→ingest; continuous spec generation. ([[20-testing]])
- [ ] T092 Governance: risky→feature branch; approved-spec→revision. ([[20-testing]])
- [ ] T093 Parity: enumerate capabilities, assert Chat and API produce identical effects. (P9; [[20-testing]])
- [ ] T094 Provenance/security: `raw/` never written; provenance chain reconstructable; secrets excluded. ([[18-security]])
- [ ] T095 Full invariant matrix in CI; block merges on failure. ([[20-testing]])

## Dependencies

- T010–T013 precede all pipeline/engine tasks.
- T030 (lifecycle) blocks T060/T061 (output usage) and T051.
- T040/T041 (risk/branch) block T020, T050 mutation paths.
- T070 blocks T071–T074 and T093.
- T093 blocked by T072 + T073.
- TBD-2, TBD-4, TBD-8, TBD-10 must be resolved before T074, T060, T020(final), T072 respectively.
