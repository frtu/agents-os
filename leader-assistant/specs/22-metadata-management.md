---
id: 202608221200-22
title: Metadata & Foundation-Doc Management
spec: 22-metadata-management
layer: moc
status: draft
lifecycle: draft
Category: spec
Tags: [metadata, foundation-docs, wiki-schema, wiki-architecture, bootstrap, extension, traceability]
traceability:
  readme: ["§10 Knowledge Layers", "§11 Zettelkasten Model", "§32 Reference Documents"]
  references: ["_references_/10-internal-storage/wiki-schema.md", "_references_/10-internal-storage/wiki-architecture.md"]
related:
  - "[[03-workspace]]"
  - "[[04-knowledge-ingestion]]"
  - "[[05-zettelkasten]]"
  - "[[007-knowledge-activities]]"
Created: 2026-08-22
Last Updated: 2026-08-22
---

# Metadata & Foundation-Doc Management

This MOC centralizes **how the foundation docs — `wiki-schema.md` and `wiki-architecture.md`
— are managed** inside each vault. These two docs are the **metadata contract** for
everything under `vault/wiki/`: `wiki-schema.md` defines the directory layout, page format,
frontmatter schema, special files, and operations; `wiki-architecture.md` defines the six
knowledge categories and their articulation (Constitution P4).

The goal is three properties that normally pull against each other:

1. **Bootstrap** — every vault starts from a shared **core** copied from `references/`.
2. **Local autonomy** — each vault may add or override rules (new paths, extra categories,
   extra frontmatter fields) to fit its own knowledge.
3. **Traceability & change transparency** — it is always obvious *what a vault changed*
   relative to the core, at a glance and by diff.

We get all three with a **two-file model per foundation doc**: a pristine **core** copy and
a separate **extension** that holds only the local deltas.

> **Terminology.** "Foundation docs" and "metadata docs" are used interchangeably for
> `wiki-schema.md` / `wiki-architecture.md`. "Core" = the immutable copy of a foundation
> doc. "Extension" = the vault-local overlay for that doc.

## 1. The two-file model

Each foundation doc exists in **two** files inside `vault/docs/`:

| Role | File | Owner | Mutability |
|------|------|-------|------------|
| **Core** | `wiki-schema.md` | shared source (`references/`) | **immutable** — never edited in the vault |
| **Extension** | `wiki-schema-extension.md` | the vault | **mutable** — the only place local rules live |
| **Core** | `wiki-architecture.md` | shared source (`references/`) | **immutable** |
| **Extension** | `wiki-architecture-extension.md` | the vault | **mutable** |

Rationale: because the **core stays byte-identical** to its source, a vault's *entire*
divergence from the shared contract is contained in the extension file. Reviewing "what did
this vault change?" is reading one file; verifying "did anyone tamper with the core?" is a
single hash/diff against `references/`. This is the change-transparency guarantee.

## 2. Folder structure

```text
vault/docs/
├── wiki-schema.md                 # CORE — copied verbatim from references/ on create; immutable
├── wiki-schema-extension.md       # EXTENSION — vault-local overrides/additions for the schema
├── wiki-architecture.md           # CORE — copied verbatim from references/ on create; immutable
└── wiki-architecture-extension.md # EXTENSION — vault-local overrides/additions for the architecture
```

See [[03-workspace]] §3.4 for how `vault/docs/` sits in the workspace, and
[[007-knowledge-activities]] for how the ingest activity consumes these docs.

## 3. Rules

- **R1 — Bootstrap from `references/` on create.** When a vault is scaffolded, the two core
  files are **copied verbatim** from the **skill library's `references/`** —
  `skills/second-brain/references/{wiki-schema,wiki-architecture}.md` (the source the skills
  were authored against; [[007-knowledge-activities]] D10). The two extension files are
  created from the extension template (§4), pre-filled only with the path overrides this
  workspace needs.
- **R2 — Core is immutable.** No process — human tooling, agent, or ingest workflow — edits a
  core file after bootstrap. The core is a faithful mirror of the shared contract; its only
  legitimate change is a **refresh** (R6).
- **R3 — All local rules live in the extension.** Any vault-specific rule (a new path, an
  extra category, an added/loosened frontmatter field, a changed special-file name) MUST be
  written in the corresponding `*-extension.md`, never in the core.
- **R4 — Extension references, extends, and overrides the core.** Each extension MUST name the
  core it overlays and MAY: (a) **add** rules the core does not cover; (b) **override** a core
  rule (e.g. path mapping `raw/ → vault/raw/`, `wiki/ → vault/wiki/`, index `→ portal.md`);
  (c) **restrict/remove** a core rule for this vault. Each entry states which core section it
  affects.
- **R5 — Resolution: extension wins.** The effective contract is `core` overlaid by
  `extension`; on any conflict, the **extension takes precedence**. Consumers MUST read both
  and apply the overlay (never the core alone). Anything not mentioned by the extension falls
  through to the core unchanged.
- **R6 — Refresh flow (upgrading the core).** When the shared `references/` doc changes, a
  vault MAY refresh: re-copy the core verbatim (R1) — the **extension survives untouched**.
  Because local deltas were never in the core, refresh is a clean overwrite; any override that
  the new core makes redundant is flagged for review but not auto-deleted. Each refresh records
  the new provenance (R7) and appends a `log.md` entry.
- **R7 — Provenance pinning.** Each core file's provenance MUST be recorded so drift/upgrades
  are detectable: the source path, a content hash, and the copied-at date (in the extension's
  header, §4). Verifying integrity = re-hash the core and compare; drift ≠ 0 means the core was
  edited in violation of R2.
- **R8 — Traceability is single-surface.** The **only** place to look for a vault's divergence
  from the shared contract is its extension files. Reviewers and the ingest activity treat the
  extension as the authoritative statement of local rules.

## 4. Extension file format

Each `*-extension.md` follows a fixed shape so overrides are machine- and human-readable:

```markdown
---
extends: wiki-schema.md            # the core doc this overlays (same folder)
source: skills/second-brain/references/wiki-schema.md   # provenance of the core (R7)
source-hash: <sha256 of the core at copy time>          # integrity/drift check (R7)
copied: 2026-08-22                 # bootstrap/refresh date (R1/R6)
---

# Wiki Schema — {workspace} extension

> Overlays `wiki-schema.md`. Extension wins on conflict (spec 22 R5). Do not edit the core.

## Path overrides
- `raw/` → `vault/raw/`
- `wiki/` → `vault/wiki/`
- index file: `wiki/index.md` → `vault/wiki/portal.md`

## Added rules
- <topic> — <new rule not present in the core, with the core section it complements>

## Overridden rules
- <core §section> — <what changes and why>

## Removed/restricted rules
- <core §section> — <what this vault does not apply, and why>
```

`wiki-architecture-extension.md` uses the same header + sections (its body groups by the six
categories rather than schema sections). The concrete override content is the vault's own;
this spec fixes only the **structure** and the **rules** around it.

## 5. Consumption

The ingest activity ([[007-knowledge-activities]]) reads **both** the core and the extension
for each foundation doc and applies the overlay (R5) before running the skill, injecting the
merged contract as runtime context. This is what lets the unmodified `second-brain-ingest`
skill resolve this vault's real paths. No consumer reads the core alone.

## 6. Acceptance Criteria

- AC1: After vault create, `vault/docs/` holds four files — `wiki-schema.md`,
  `wiki-schema-extension.md`, `wiki-architecture.md`, `wiki-architecture-extension.md`. (R1)
- AC2: The two core files are **byte-identical** to
  `skills/second-brain/references/{wiki-schema,wiki-architecture}.md` at bootstrap. (R1)
- AC3: Core files are never modified after bootstrap; their recorded `source-hash` still
  matches their content (drift = 0), except immediately after an explicit refresh. (R2, R7)
- AC4: Each extension declares `extends`, `source`, `source-hash`, `copied`, and contains the
  Path-overrides / Added / Overridden / Removed sections. (R3, R4, R7)
- AC5: The effective contract applies the extension over the core with **extension-wins**
  precedence; unmentioned rules fall through to the core. (R5)
- AC6: A refresh re-copies the core and leaves the extension untouched; provenance is updated
  and a `log.md` entry is appended. (R6, R7)
- AC7: A vault's entire divergence from the shared contract is readable from its extension
  files alone (single-surface traceability). (R8)

## 7. Constitution & spec alignment

- **P4 (Zettelkasten discipline)** — the internal-storage contract (`wiki-schema.md`,
  `wiki-architecture.md`) remains binding for `vault/wiki/`; this spec governs *how* that
  contract is instantiated and locally adapted without losing it.
- **P10 (portability & durability)** — plain Markdown + YAML; the two-file model is fully
  git-diffable, no proprietary format.
- **[[03-workspace]] §3.4** — defines the `vault/docs/` location; this MOC is the authority on
  the rules/lifecycle of the files within it.
- **[[007-knowledge-activities]]** — the ingest activity is the primary consumer (R1 bootstrap
  source, R5 overlay, §5 consumption); FR-9/FR-10/FR-11 there implement this MOC.
