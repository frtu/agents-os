---
id: 202608152112-03
title: Workspace
spec: 03-vault
layer: moc
status: draft
lifecycle: draft
Category: spec
Tags: [workspace, vault, storage, git, directory-structure, provenance]
traceability:
  readme: ["§6 Git as the Knowledge and Specification Ledger", "§10 Knowledge Layers", "§27 Portal and Log"]
  references: ["_references_/10-internal-storage/wiki-schema.md#architecture", "_references_/10-internal-storage/wiki-architecture.md"]
related:
  - "[[02-domain-model]]"
  - "[[04-knowledge-ingestion]]"
  - "[[05-zettelkasten]]"
  - "[[11-git-workflow]]"
Created: 2026-08-15
Last Updated: 2026-08-16
---

# Workspace

A **Workspace** is the top-level container the assistant operates on. Each workspace is a
**Git repository** and holds three children: `skills/` (installed skills), `sessions/`
(short-term conversations), and `vault/` (the ingestion root — the durable knowledge store).
The **vault** is where all durable knowledge lives; every meaningful mutation is a Git commit.
This spec defines the physical layout; [[04-knowledge-ingestion]], [[05-zettelkasten]], and
[[06-conversations]] define how the vault is populated.

> **Terminology.** "Workspace" is the container and unit of multiplicity. "Vault" is the
> `vault/` subfolder inside a workspace — the ingestion root / knowledge store. The word
> "vault" throughout the spec kit refers to that subfolder, never the container.

> **Code divergence (target vs. current).** These docs describe the **target** model. The
> current app code and tests still use the previous names: a flat `Vaults/<name>/` container
> (no `vault/` nesting, no `skills/`), env vars `LEADER_VAULT_ROOT` / `LEADER_VAULT_PATH` /
> `LEADER_DEFAULT_VAULT`, default name `default`, the `vault` API field, and `/api/vaults`
> endpoints. Treat the spec as the migration target, not a description of what is implemented.

> Layout differences vs. the remote source (top-level `source/`, per-workspace templates) are
> recorded in [[03-vault-contradiction]]. Local is authoritative.

## 0. Multi-Workspace (Constitution P13)

The assistant supports **multiple workspaces** under a configurable root:

- Default root `Workspaces/`; each workspace at `Workspaces/<workspace-name>/`.
- A `_default_` workspace is created by default when no selector is supplied.
- Overridable via environment: `LEADER_WORKSPACE_ROOT` (root dir, default `./Workspaces`),
  `LEADER_WORKSPACE_PATH` (explicit single-workspace path), `LEADER_DEFAULT_WORKSPACE` (default
  selector, default value `_default_`).
- Any `LEADER_*` variable may be set in a repo-root `.env` file, loaded once at process
  startup (`app/__main__.py`). A real shell/CLI environment value always wins over `.env`
  (loaded with `override=False`), so `.env` is a convenience default an operator can override.
- Every capability resolves a target workspace from an explicit selector, or the configured
  default when omitted ([[13-api]], [[14-chat]]).
- All durable state for a workspace stays inside that workspace. **Output templates are the
  exception** — they live in an externalized repo-root `templates/` shared across workspaces (§6b).

## 1. Top-Level Layout

```text
Workspaces/<workspace-name>/
├── skills/         # installed skills — each a file/folder or a reference-link to another folder
├── sessions/       # operational conversations (short-term memory)
└── vault/          # ingestion root — the durable knowledge store
    ├── raw/        # human-owned sources (captured; never modified by the pipeline)
    ├── wiki/       # LLM workspace — all durable knowledge
    ├── docs/       # foundation docs (copied on create) + per-workspace extensions
    └── output/     # generated artifacts (reports, query results)

templates/          # repo-root, externalized, shared output templates (NOT inside a workspace)
```

## 1.1 Bootstrap Template (copied on create)

A repo-root **workspace bootstrap template** at `templates/_workspace_/` seeds every new
workspace. On create, the scaffolder **copies the template's contents** (e.g. `bootstrap.sh`,
`.gitignore`) into the new workspace root and then **runs `bootstrap.sh`** from inside the
workspace. The template is referenced by a **repo-relative** path (never an absolute one), and
the copy is **non-destructive/idempotent** — an existing file in the workspace is never
overwritten.

`bootstrap.sh` links the shared skill library into the workspace's `skills/` folder (§2). Its
execution is **best-effort**: a missing skill library (e.g. in an isolated test root) makes it a
no-op rather than failing workspace creation. A missing template folder likewise skips this step.

## 2. `skills/` — Installed Skills

Each workspace has a `skills/` folder holding its **installed skills**. Skills are
workspace-scoped, so different workspaces can install different skill sets. Each entry is either:

- **Self-contained** — a skill file or folder that lives directly under `skills/`; or
- **A reference-link** — a pointer to a skill folder maintained elsewhere (a shared skill
  library), realized as a **symlink** `skills/<name>` → the library's `<name>/` folder.

### 2.1 Reference-link import & discovery (feature [[005-skill-import]])

Feature 005 decides the previously-TBD import/loading mechanism:

- **Shared library.** Available skills live in a **shared skill library** — a local folder
  resolved from `LEADER_SKILLS_SOURCE` (default: the repo-sibling `skills/`). Each skill is a
  `<name>/SKILL.md` folder.
- **Import = reference-link (plan-first).** Installing a skill from chat is **consequential**:
  it returns a plan and, on approval (P8), creates a symlink `skills/<name>` → `<library>/<name>`
  and commits it to the workspace git repo. Imports are **idempotent** (a dangling link is
  re-pointed, not duplicated). Names are validated against path traversal and must resolve to an
  existing `<library>/<name>/SKILL.md`.
- **Discovery mirror.** Because the chat agent runtime discovers skills from
  `.claude/skills/<name>/SKILL.md`, the canonical `skills/<name>` link is mirrored by a second
  symlink `.claude/skills/<name>` → the same library folder. Both are created together from one
  source, satisfying the spec layout and the runtime discovery path.
- **Enumeration.** The assistant enumerates **installed** skills from the entries under
  `skills/`, and **available** skills by scanning the library for `<name>/SKILL.md` (each with a
  `description` parsed from the SKILL.md frontmatter and an `installed` flag).
- **Execution.** Once installed, the agent **dynamically discovers and runs** skills on later
  turns (no restart), with a workspace-scoped tool set. This deliberately expands the agent's
  tools beyond citations-only browse (feature 002 D3); `vault/raw/` immutability (P2) is then
  enforced for the agent by a raw-guard hook, with the per-workspace git repo as backstop (see
  [[005-skill-import]] D3).

## 3. `vault/` — Ingestion Root (Knowledge Store)

The vault is the durable knowledge store and holds four subfolders: `raw/` (immutable,
human-owned sources), `wiki/` (synthesized durable knowledge), `docs/` (foundation +
extension docs for the ingestion activity, §3.4), and `output/` (generated artifacts). The
provenance chain flows `vault/raw/ → sessions/ → vault/wiki/`.

### 3.1 `vault/raw/` — Human-Owned Sources (the capture target)

Properties: provenance-preserving, source of truth, ingestion-triggering, never treated as
synthesized knowledge. **Humans own `vault/raw/`**: they may add, modify, or delete these files,
and the app provides tools to help them do so through the **capture** channel (Constitution P2,
features [[004-assistant-sidebar]] and [[007-knowledge-activities]]). **Capture** is an input
mechanism only — it deposits a source into `vault/raw/<provenance>/` and performs **no knowledge
processing**. The **ingest workflow / LLM reads but never modifies** these files — all automated
processing produces new files downstream (see [[04-knowledge-ingestion]] for how captured sources
become knowledge).

Canonical subdirectories:

- `vault/raw/assets/` — images/audio referenced with `![[resource/path]]`.
- `vault/raw/clippings/` — web articles (Obsidian Web Clipper or manual).
- `vault/raw/docs/` — PDFs, papers, received reference files.
- `vault/raw/notes/` — handwritten notes, briefs, ideas.
- `vault/raw/transcripts/` — meeting/voice/interview transcripts.

Arbitrary subdirectories are allowed; all are ingestion candidates. The `{provenance}` subpath
under `vault/raw/` is preserved through the whole chain.

### 3.2 `vault/wiki/` — Durable Knowledge Workspace

Six categories (see [[02-domain-model]] §2). Directory map:

```text
vault/wiki/
├── sources/
│   ├── _daily_/                 # daily digests (dreaming output)
│   └── {provenance}/            # source summaries mirroring vault/raw/
├── concepts/{patterns,technologies}/
├── product/{persona,entities,features}/
├── product/specs/               # the assistant's RUNTIME spec kit (00-02 core, 03+ MOCs)
├── people/{processes,steps,roles,competencies,members}/
├── resources/{artifacts,components,dependencies,tools}/
├── projects/{initiative}|{product}/{project}/
├── synthesis/
├── portal.md                    # master catalog (updated every ingest)
├── tbd.md                       # unprocessed-work backlog, sectioned by topic & theme
└── log.md                       # append-only operational record
```

> **Path note (README §32 precedence):** the assistant's runtime spec kit lives at
> `vault/wiki/product/specs/` per wiki-schema, even though README §31 writes it as `wiki/specs/`.
> This build spec kit (the one you are reading) lives at the repo-level `specs/` and is separate.

Rule: always write into the **most specific** subfolder that fits; fall back to the parent only
when none matches.

### 3.3 `vault/output/` — Generated Artifacts

Reports, query results, exported deliverables. May feed back into knowledge via
[[15-integrations]] §Output→Knowledge. Produced by reusing templates from the root `templates/`
folder (§6b, [[21-outputs]]).

### 3.4 `vault/docs/` — Foundation & Extension Docs

The ingestion **activity** (the `second-brain-ingest` skill, [[007-knowledge-activities]]) expects
foundation docs describing the wiki schema and architecture. Rather than have the app rewrite the
skill, each workspace carries these docs locally so the activity can read them at runtime. Their
lifecycle and rules (bootstrap, immutable core, extension overlay, traceability) are governed by
[[22-metadata-management]] — this section defines only the folder location.

```text
vault/docs/
├── wiki-schema.md                 # foundation — COPIED verbatim on create; never modified
├── wiki-architecture.md           # foundation — COPIED verbatim on create; never modified
├── wiki-schema-extension.md       # per-workspace override; references the foundation
└── wiki-architecture-extension.md # per-workspace override; references the foundation
```

- **Foundation docs** (`wiki-schema.md`, `wiki-architecture.md`) are copied from the shared source
  on workspace create and are **immutable** — the workspace never edits them, so the shared truth
  stays consistent across workspaces (option (b)).
- **Extension docs** (`*-extension.md`) are per-workspace. They **reference** the foundation and may
  **extend or override** it — chiefly to reconcile the activity's assumed layout with this
  workspace's real layout (`raw/ → vault/raw/`, `wiki/ → vault/wiki/`, index `→ vault/wiki/portal.md`).
- The activity wrapper injects these docs as runtime context so the skill runs **unmodified**
  ([[007-knowledge-activities]]).

## 4. `sessions/` — Short-Term Memory

Ephemeral operational conversation logs at the **workspace level** (a sibling of `vault/`, not
inside it). Not part of the wiki. Feed the dreaming pipeline. See [[06-conversations]].

One file per thread, named `YYYY-MM-DD-HH-MM-SS-<conversation-id>-<slug>.md` (the `Created`
timestamp, to the second) and created only on the first user message
([[012-conversation-naming]] FR-1/FR-2/FR-12).

## 5. Special Files

- `vault/wiki/portal.md` — one line per page (`- [[page|Page]] — summary`, <120 chars), grouped
  by category. Updated on every ingest. See [[17-observability]].
- `vault/wiki/log.md` — append-only entries `## [YYYY-MM-DD] operation | Title`. Never edit
  existing entries.
- `vault/wiki/tbd.md` — maintained backlog of **unprocessed** `vault/wiki/` changes, classified
  by section (topic & theme); drives ingest's selection of unprocessed work
  ([[007-knowledge-activities]] FR-14/FR-15).

## 6. Git as Ledger

The workspace is a Git repository; every mutation is committed: raw ingestion metadata, source
creation/updates, concept create/modify/delete, specification changes, conversation capture,
generated artifacts. Git provides history, diffs, branches, rollback, review, merge. See
[[11-git-workflow]].

## 6b. `templates/` — Externalized Output Templates (repo root)

Reusable **output** structures (meeting summary, doc review, engineering ticket, strategy,
project summary) live in a **repo-root `templates/` folder outside any workspace**, so humans can
review and evolve them independently (Constitution P7). The assistant reads them first
(reuse-before-create) and proposes new templates only on no-match. See
[`templates/README`](../templates/README.md) and [[21-outputs]]. Whether a new workspace inherits
copies is open — [[001-leader-assistant/plan-tbd|plan-tbd]] TBD-5.

## 7. Acceptance Criteria

- AC1: The three workspace children (`skills/`, `sessions/`, `vault/`) exist with the roles above;
  the vault holds `raw/`, `wiki/`, `docs/`, `output/`; the repo-root `templates/` folder exists
  outside any workspace.
- AC2: No process ever writes to files under `vault/raw/` (the pipeline/LLM never mutates it); the
  only sanctioned writer is the **capture** channel acting on a human's behalf (P2).
- AC9: On create, `vault/docs/` contains verbatim copies of the foundation docs (`wiki-schema.md`,
  `wiki-architecture.md`) plus the two extension docs (`wiki-schema-extension.md`,
  `wiki-architecture-extension.md`); the foundation copies are never modified thereafter (§3.4).
- AC6: A workspace is resolvable by selector or default (`_default_`);
  `LEADER_WORKSPACE_ROOT`/`LEADER_WORKSPACE_PATH`/`LEADER_DEFAULT_WORKSPACE` are honored (P13).
- AC3: `vault/wiki/portal.md` reflects every wiki page after an ingest.
- AC4: `vault/wiki/log.md` is strictly append-only (enforced/verified).
- AC5: The provenance chain in [[02-domain-model]] §5 is reconstructable for any wiki concept.
- AC7: A workspace exposes an installable `skills/` folder; entries may be files or reference-links.
- AC8: Importing a skill (feature [[005-skill-import]]) creates a symlink `skills/<name>` and a
  discovery mirror `.claude/skills/<name>`, both resolving to `<library>/<name>`, and is
  committed to git; the agent then loads and runs it on a later turn without a restart.
- AC10: On create, the contents of the repo-relative bootstrap template `templates/_workspace_/`
  are copied verbatim into the new workspace (without overwriting existing files) and
  `bootstrap.sh` is run from the workspace; a missing template folder or skill library degrades to
  a no-op rather than failing creation (§1.1).
