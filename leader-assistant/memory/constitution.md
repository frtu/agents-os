# Leader Assistant Constitution

The non-negotiable principles for the **AI Product Owner / Project Specification Assistant** — an assistant that maintains a compounding Zettelkasten Knowledge Vault and continuously derives project specifications (and, secondarily, PO/PM artifacts) from it. Every spec, plan, and task in this repository MUST comply. When a plan conflicts with the constitution, the constitution wins; amend the constitution deliberately rather than working around it.

> **Derivation.** This constitution is derived from the remote Leader Assistant constitution (10 principles) and customized to this repository's local spec kit (`specs/00`–`specs/20`). Where the local spec set and the remote source disagree, the local intent is authoritative and the conflict is recorded in a `specs/NN-*-contradiction.md` file; unresolved decisions are indexed in [`specs/clarification.md`](../specs/clarification.md).

Version: 1.1.1 · Ratified: 2026-08-16 · Last amended: 2026-08-22

> **Amendment 1.1.1 (2026-08-22).** Principle 2 clarified with terminology: the human-owned input channel into `vault/raw/` is named **capture** — an input mechanism that deposits sources *without any knowledge processing*. This is distinguished from **ingest**, the internal *workflow* that reads captured sources and derives durable knowledge (`vault/raw/ → vault/wiki/`). No principle changed; the two words are now used consistently across the spec kit. Motivated by feature [`007-knowledge-activities`](../specs/007-knowledge-activities/spec.md).
>
> **Amendment 1.1.0 (2026-08-16).** Principle 2 clarified: `vault/raw/` is *human-owned* — the app may help a human add/modify/delete raw sources — while the **internal ingestion pipeline** remains forbidden from mutating `vault/raw/`. Motivated by feature [`004-assistant-sidebar`](../specs/004-assistant-sidebar/spec.md) (local file upload into `vault/raw/`).

---

## Principle 1 — The Vault is the source of truth

All durable knowledge lives in a **vault** — the `vault/` folder of a workspace — as plain-text Markdown, not in application state, chat history, or a database. Anything worth keeping is written to a file. If it is not in the vault, it does not exist for the assistant.

- Vaults are plain-text, Obsidian-compatible, and git-versionable.
- **Multiple workspaces are supported** (see Principle 13); each holds one vault. Capabilities operate on a selected workspace's vault.

Source specs: [[03-workspace]], [[19-non-functional]].

## Principle 2 — `vault/raw/` is human-owned; the pipeline never mutates it

Sources in `vault/raw/` are the source of truth for provenance and the entry point of the knowledge pipeline. **Humans may add, modify, or delete files in `vault/raw/`**, and the app SHOULD provide tools to help them manage these sources through the **capture** channel — an input mechanism that deposits sources into `vault/raw/<provenance>/` *without any knowledge processing* (no summarizing, classification, or wiki mutation). In contrast, the **internal ingestion process and the assistant/agent MUST NEVER modify, rewrite, or delete files in `vault/raw/`**: **ingest** — the internal workflow — only *reads* `vault/raw/` and writes *new* files downstream (`vault/wiki/sources/`, then `vault/wiki/`). The `{provenance}` subpath under `vault/raw/` is preserved through the whole knowledge chain.

- **Capture** = deposit into `vault/raw/` (human-owned input; no processing).
- **Ingest** = the internal workflow that derives knowledge from captured sources (`vault/raw/ → vault/wiki/`); never writes back into `vault/raw/`.

Source specs: [[03-workspace]], [[04-knowledge-ingestion]], [[18-security]].

## Principle 3 — The pipeline has one direction

Knowledge flows in one direction and each stage has a distinct role that MUST NOT be skipped for durable knowledge:

```text
vault/raw/ → sessions/ → (dreaming) → vault/wiki/sources/_daily_/ → (ingest)
     → vault/wiki/sources/{provenance}/ → vault/wiki/{category}/
vault/wiki/ + templates/ → vault/output/
```

- `vault/raw/` — immutable ingested sources.
- `sessions/` — ephemeral operational conversation logs (short-term memory), at the workspace level.
- **dreaming** — daily/on-demand compaction of sessions into `vault/wiki/sources/_daily_/`.
- `vault/wiki/sources/{provenance}/` — one factual summary page per ingested source, mirroring `vault/raw/` for provenance.
- `vault/wiki/{category}/` — atomic, interlinked Zettelkasten knowledge (the compounding asset).
- `templates/` — reusable **output** structures, externalized at repo root (Principle 7).
- `vault/output/` — produced artifacts.

> This is the **local** pipeline (richer than the remote flat `raw → source → wiki`). The divergence is recorded in [[04-knowledge-ingestion-contradiction]] and [[03-vault-contradiction]].

Source specs: [[04-knowledge-ingestion]], [[06-conversations]], [[02-domain-model]].

## Principle 4 — Zettelkasten discipline in `vault/wiki/`

Concepts are written, not collected. Every `vault/wiki/` page MUST:

- Capture **one** idea (atomicity), in the assistant's own words — never copy-paste from the source.
- Have a stable time-based identity (`id`, `YYYYMMDDHHMM`) decoupled from its filename, and be reachable via `[[wikilinks]]`.
- State the **why** of each link (link context), not just the link.
- Follow the internal-storage contract in `_references_/10-internal-storage/` (`wiki-schema.md`, `wiki-architecture.md`), which is binding for everything under `vault/wiki/`.

Connection is prioritized over collection: a new concept that links to nothing is incomplete.

Source specs: [[05-zettelkasten]], [[02-domain-model]].

## Principle 5 — Concept lifecycle is evidence-based

Every `vault/wiki/` concept carries a `status` that reflects proven usefulness, promoted only by real usage:

- `draft` — newly created or substantially changed.
- `used` — referenced by an output **≥ 3 times**.
- `reliable` — used **> 8 times without a big correction**.

Rules:

- Promotion is automatic and derived from evidence (`usage-count` / `referenced-to`), never asserted by hand.
- A **big correction** — a substantive change to the concept's body, not a typo or formatting fix — resets the clean-usage streak, records `last-correction`, and demotes `reliable → used`.
- Status MUST always be justifiable from the page's own frontmatter.

Source specs: [[05-zettelkasten]], [[02-domain-model]].

## Principle 6 — Traceability is mandatory (bidirectional links)

Any artifact can be traced to its evidence and any concept to its impact:

- Every `vault/output/` artifact (and every specification) cites the `vault/wiki/` concepts it used, via `[[wikilinks]]`.
- Every `vault/wiki/` concept records the artifacts it contributed to in its `referenced-to` list, and increments `usage-count`.
- Every ingestion, dreaming, production, spec, and lint operation is appended to the vault's `log.md` (`vault/wiki/log.md`); existing log entries are never edited.

Source specs: [[05-zettelkasten]], [[11-git-workflow]], [[17-observability]].

## Principle 7 — Reuse before create (externalized templates)

When producing an output, the assistant MUST first search `templates/` for the closest matching template and reuse it. Creating a new template is allowed only when no close match exists, and MUST be proposed to the user before adoption. The same bias applies to concepts: prefer updating an existing `vault/wiki/` page over creating a near-duplicate.

- Templates live in a **dedicated, externalized folder at the repository root** (`templates/`), so humans can review and evolve them independently of the assistant.

Source specs: [[21-outputs]], [[15-integrations]].

## Principle 8 — Human-in-the-loop for consequential work

The assistant proposes; the human curates. Consequential work — anything the Risk Engine flags, external PM actions, and destructive changes — requires a plan the user can review before execution. Operations that mutate `vault/wiki/` surface their intent and key takeaways for review. Routine autonomous operations (ingestion, dreaming, lint, draft generation) may proceed without a plan, recording their effects in portal/log/git.

Source specs: [[09-planning]], [[10-risk-engine]], [[18-security]].

## Principle 9 — Interface parity (API == chat)

The assistant is reachable via REST API and application chat. Both interfaces expose the **same** capabilities operating on the **same** workspaces; neither is a second-class citizen, and neither may bypass the planning/risk/knowledge model. Any capability added to one MUST be available to the other.

Source specs: [[12-assistant]], [[13-api]], [[14-chat]].

## Principle 10 — Portability and durability

No lock-in. The vault must remain fully usable with nothing but a text editor and Obsidian:

- Plain Markdown + YAML frontmatter only; no proprietary formats; vector embeddings are never the canonical knowledge model.
- Links are `[[wikilinks]]`; internal references never use raw absolute paths inside page content.
- The workspace is a git repo — history, review, and rollback come for free.

Source specs: [[19-non-functional]], [[11-git-workflow]].

## Principle 11 — Continuous specification generation

Specifications are the primary product output. They evolve **continuously from knowledge changes**, not from an explicit "generate the specification" command: a knowledge change triggers impact analysis, which drafts or updates the affected specs. Specifications form a linked graph and carry their own semantic lifecycle (`draft → review → approved`); an **approved** spec is never silently overwritten — changes become a new proposed revision.

Source specs: [[00-product-vision]], [[07-specification-model]], [[08-specification-lifecycle]].

## Principle 12 — Risk-governed mutations

Every proposed mutation is evaluated by an **extensible Risk Engine whose rules are declared as data** (`id, scope, condition, severity, action`), not hard-coded branches. Safe changes commit to `main`; risky changes go to a `feature/{name}` branch and are **never silently merged** without the approval policy being satisfied. Each evaluation is auditable in `log.md`.

Source specs: [[10-risk-engine]], [[11-git-workflow]].

## Principle 13 — Multi-workspace

The assistant supports multiple workspaces under a configurable root (default `Workspaces/`, each workspace at `Workspaces/<workspace-name>/`; overridable via environment). A `_default_` workspace is created by default. Every capability resolves a target workspace (an explicit selector, or the configured default when omitted). All durable state for a workspace stays inside that workspace.

Source specs: [[03-workspace]], [[02-domain-model]].

---

## Amendment process

Amendments require: (1) a stated rationale, (2) a version bump (semver: MAJOR for principle removal/redefinition, MINOR for a new principle, PATCH for clarifications), and (3) a note of downstream specs that must be reconciled. Record amendments in affected workspaces' `log.md` where relevant.

## Compliance

Every `plan.md` MUST include a "Constitution Check" section confirming alignment with these principles (or justifying a deviation). Reviews reject work that violates a principle without an approved amendment. Open questions and deferred decisions are tracked in [`specs/clarification.md`](../specs/clarification.md).
