# Implementation Plan: Leader Assistant

**Feature ID:** `001-leader-assistant` · **Spec:** the local spec set [`specs/00`–`specs/21`](../README.md)
**Status:** Draft
**Created:** 2026-08-16 · **Last Updated:** 2026-08-16

> Describes **how** to build the assistant specified by the 21-document local spec kit. Requirements are referenced, not restated. Open technical choices are recorded in [`plan-tbd.md`](plan-tbd.md) — this plan pins only what is decided. Illustrative endpoint URLs below are **not binding**; the binding constraint is capability parity (P9).

## Scope

This single feature folder is the buildable layer over the whole local spec set. The **spec** is the numbered docs; this **plan** turns them into a concrete stack and architecture; [`tasks.md`](tasks.md) is the ordered build.

## Constitution Check

- [x] **P1 Vault is source of truth** — all durable state is Markdown in the vault; no DB. ([[03-vault]])
- [x] **P2 `raw/` immutable** — vault access layer rejects writes under `raw/`. ([[18-security]])
- [x] **P3 Pipeline direction** — orchestrators enforce `raw → sessions → dreaming → wiki/sources → wiki/category`; `wiki + templates → output`. ([[04-knowledge-ingestion]], [[06-conversations]])
- [x] **P4 Zettelkasten discipline** — schema helpers enforce id/atomicity/link-context per `wiki-schema.md`. ([[05-zettelkasten]])
- [x] **P5 Concept lifecycle** — pure `lifecycle` functions derive `status` from `usage-count`/`last-correction`. ([[05-zettelkasten]])
- [x] **P6 Traceability** — outputs cite concepts; concepts gain `referenced-to` + `usage-count`; `log.md` append-only. ([[17-observability]])
- [x] **P7 Reuse before create** — output engine reads root `templates/` first; new template proposed to user. ([[21-outputs]])
- [x] **P8 Human-in-the-loop** — planning + risk gate consequential work; confirmation surfaced before wiki mutations. ([[09-planning]])
- [x] **P9 Interface parity** — one surface-agnostic capability layer behind both REST and chat. ([[12-assistant]], [[13-api]], [[14-chat]])
- [x] **P10 Portability** — Markdown + YAML + git only; `[[wikilinks]]`; no vector store as canonical. ([[19-non-functional]])
- [x] **P11 Continuous specification generation** — spec engine reacts to knowledge changes; approved-spec protection. ([[07-specification-model]], [[08-specification-lifecycle]])
- [x] **P12 Risk-governed mutations** — rules-as-data risk engine; risky → `feature/{name}`; no silent merge. ([[10-risk-engine]])
- [x] **P13 Multi-vault** — vault resolver honors `Vaults/<name>/` + env overrides + default selector. ([[03-vault]])

## Technical Context (decided)

- **Language / runtime:** Python 3.11+.
- **Agent runtime:** `claude-agent-sdk` with `Read`, `Glob`, `Grep`, `Write`, `Edit` tools **scoped to the active vault**; resumable sessions (pass-through `session_id`); partial-message streaming. Assistant behavior driven by system-prompt sections derived from the numbered specs.
- **REST:** FastAPI (JSON in/out; SSE for streaming).
- **Chat UI:** Gradio, mounted on the **same** FastAPI app (single server).
- **Storage:** filesystem only — Markdown + YAML frontmatter, Obsidian-compatible, git-versioned. **No database, no vector store** (P1/P10). Optional on-device search (`qmd`) is a later, non-canonical add-on (see `plan-tbd.md`).
- **Capability layer:** a single, surface-agnostic Python module both REST and chat call — the parity boundary (P9).
- **Dependencies:** none upstream; this is the whole app.

> Rationale for adopting this stack: it is the concrete, proven choice from the remote spec kit and satisfies every constitutional constraint. The local spec deliberately deferred implementation detail ([[13-api]]); this plan supplies it without changing the domain model.

## Architecture Overview

```text
        REST (FastAPI)  ┐
        Chat (Gradio)   ┘── shared capability layer ──▶ engines ──▶ Vault (git)
                                                        │
   Knowledge · Ingestion · Zettelkasten · Specification · Planning ·
   Risk · Workflow/Execution · Git/Vault · Integration
```

Engines and their responsibilities are specified in [[12-assistant]]. The capability layer is the only path from an interface to an engine (P9); engines are the only path to the vault.

## Components

- **`vault` (resolver + guard):** resolves `Vaults/<name>/` from a selector or the default; honors `LEADER_VAULT_ROOT` / `LEADER_VAULT_PATH` / `LEADER_DEFAULT_VAULT`; scaffolds a new vault; rejects any write path under `raw/`. (P1, P2, P13)
- **`ingestion`:** event-driven raw → source-summary → concept flow; classifier (subfolder + content sniff); invokes risk + git; updates portal/log. ([[04-knowledge-ingestion]])
- **`dreaming`:** sessions → `wiki/sources/_daily_/` digests. ([[06-conversations]])
- **`zettelkasten`:** id/atomicity/link-context enforcement; dedup pre-check. ([[05-zettelkasten]])
- **`lifecycle` (status engine):** pure functions `compute_status(fm)`, `record_usage(concept, output_link)`, `record_big_correction(concept, date)`; owns `usage-count`/`referenced-to`/`last-correction`. ([[05-zettelkasten]])
- **`specification`:** continuous generation, impact analysis, spec graph, semantic lifecycle, approved-spec protection. ([[07-specification-model]], [[08-specification-lifecycle]])
- **`planning`:** plan-first for consequential work. ([[09-planning]])
- **`risk`:** rules-as-data evaluation → commit-main | feature-branch | require-approval | reject. ([[10-risk-engine]])
- **`output`:** reuse-before-create against root `templates/`; writes `output/`; records citations + usage. ([[21-outputs]])
- **`git`/vault manager:** commit conventions, branch policy, append-only log. ([[11-git-workflow]])
- **`capabilities`:** surface-agnostic entry points (below).

## Data & File Contracts

Vault layout, categories, portal/log formats: [[03-vault]], [[02-domain-model]] (authoritative). Concept frontmatter extends the schema with lifecycle fields:

```yaml
status: draft            # draft | used | reliable
usage-count: 0           # counter — increments per output that cites the concept
referenced-to: []        # list of [[output/spec links]] — the references
last-correction:         # YYYY-MM-DD, empty until first big correction
```

Lifecycle math (authoritative in [[05-zettelkasten]]): `clean_uses` counted since `last-correction` (or creation); `reliable` if `clean_uses > 8`, else `used` if `usage-count ≥ 3`, else `draft`; a big correction sets `last-correction=today` and demotes `reliable → used`.

## Interfaces / Contracts

Surface-agnostic capability functions (both REST and chat call these — the parity boundary):

- `list_vaults()` / `create_vault(name)` / resolve-default
- `ingest(vault, source_ref) -> IngestReport`
- `dream(vault) -> DigestReport`
- `query(vault, question) -> Answer` (cited)
- `plan(vault, request) -> Plan` / `execute(vault, plan) -> Result`
- `produce(vault, request) -> OutputReport` (reuse-before-create)
- `ask(vault, message, session_id) -> Answer` (agent, streamable)
- `lint(vault) -> LintReport`
- `spec_read/spec_transition(vault, id, state)`

> REST paths and the exact HITL-over-REST mechanism are **not fixed here** — see [`plan-tbd.md`](plan-tbd.md). The remote's concrete `/api/...` URLs are treated as disposable illustration.

## Alternatives Considered

- **Vector RAG / sidecar DB** — rejected; violates P1/P10. Portal index + optional `qmd` suffice at target scale.
- **Per-vault `templates/`** (remote) — rejected in favor of a single externalized root `templates/` so humans evolve one reviewable set (P7); recorded in [[03-vault-contradiction]].
- **Flat `raw → source → wiki`** (remote) — not adopted; local keeps `sessions/` + dreaming + `wiki/sources/` provenance mirror ([[04-knowledge-ingestion-contradiction]]).

## Risks & Mitigations

- **Concept sprawl** → update-over-create + periodic lint. ([[17-observability]])
- **HITL across stateless REST** → open; options in `plan-tbd.md`.
- **Miscounted usage** → only the `lifecycle` engine writes `usage-count`.

## Rollout / Sequencing

MVP: single vault, markdown ingestion, concept create + portal/log, lifecycle frontmatter (`status` stays `draft`), `query`, chat `ask`. Then: multi-vault resolution, dreaming, promotion/demotion, risk-branching, continuous spec generation, output/template reuse, REST surface + parity tests.
