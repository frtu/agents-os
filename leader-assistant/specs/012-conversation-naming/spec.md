# Feature Specification: Conversation Naming & Lazy Session Creation

**Feature ID:** `012-conversation-naming`
**Status:** Implemented
**Created:** 2026-08-30 · **Last Updated:** 2026-08-30

> Describes **what** and **why**. A session file becomes a **named, dated, human-readable record**
> (`YYYY-MM-DD-<conversation-id>-<slug>.md`) that comes into existence **only once the user has
> actually said something**, with its header rendered from the human-owned
> `templates/template-conversation.md` and its title chosen by the assistant **during the turn that
> was already running** — no extra model round trip, no added latency.
> Primary spec references: [[02-domain-model]], [[03-workspace]], [[06-conversations]],
> [[21-outputs]], and features [[002-assistant-chat]], [[006-mcp-capability-tools]],
> [[008-agent-user-interaction]].
> Amends no constitutional principle. Exercises **P1** (the file is the source of truth), **P7**
> (reuse the externalized template rather than hardcoding the shape) and **P2** (writes still pass
> `vault.guard_write_path`).

## Problem (why this feature exists)

1. **The filename contract already exists in the spec kit; the code diverged from it.**
   [[02-domain-model]] §Storage Map specifies `sessions/YYYY-MM-DD-*.md` and [[06-conversations]] §1
   gives `sessions/2026-08-12-project-spec.md` as the example. `conversation.path_for`
   (`app/conversation.py:69`) returns `sessions/<conversation-id>.md` — an opaque 12-hex name with no
   date and no subject. A human browsing `sessions/` cannot tell one conversation from another, and
   the `sessions/` folder is explicitly a **human-readable** operational record. **This feature
   restores spec compliance rather than changing the contract.**

2. **A conversation file is created by merely looking.** `conversation.load_or_create`
   (`app/conversation.py:153-168`) writes a frontmatter-only file the instant an id is resolved, and
   several **read** paths resolve ids: `concierge._pending_record` (`app/concierge.py:547`) and
   `concierge._pending_plan_record` (`:557`) both call `load_or_create` to answer "is anything
   pending?". A status poll or a sidebar refresh against an id that never had a message therefore
   leaves a permanent, empty, turn-less record behind. Those records then show up in the Sessions
   panel as real conversations, because `list_conversations` cannot distinguish them.

3. **The externalized template has no code consumer.** `templates/template-conversation.md` documents
   the intended session shape — capitalized frontmatter keys, a `Tags:` line, an
   `# Conversation — <name>` H1 — but `conversation._render_frontmatter` (`:76-85`) hardcodes
   lowercase keys and emits neither tags nor a name. The template is therefore decorative: a human
   editing it changes nothing. This violates the reuse-before-create intent of Constitution **P7**
   and [[21-outputs]] §3, and it guarantees drift between the documented shape and the written one.

4. **Listing is coupled to the filename encoding the id.** `capabilities.list_conversations`
   (`app/capabilities.py:838`) calls `convo.load(workspace, p.stem)` — it recovers the conversation
   id from the *filename*. Any richer filename breaks listing, which is what makes (1) load-bearing
   rather than cosmetic.

## User Scenarios

**S1 — a browsable session folder.** A product owner opens `Workspaces/interviews/sessions/` in
Finder and sees `2026-08-28-9b200915379e-onboarding-interview-questions.md`. They know what it is
without opening it, and files sort chronologically.

**S2 — an abandoned draft leaves nothing.** The operator opens the chat panel, the UI polls
`/api/chat/status` and refreshes the Sessions list, and then the operator closes the tab without
typing. `sessions/` is unchanged — no empty record, nothing in the Sessions panel.

**S3 — the assistant titles the conversation it is already answering.** The user asks "how should we
price the search catalog?". While composing its first reply the assistant calls `name_conversation`
with a title and tags; the record lands as `2026-08-30-<id>-search-catalog-pricing.md`, tagged
`[pricing, catalog]`. The reply arrives no later than it otherwise would.

**S4 — offline, the name is still meaningful.** With no agent runtime reachable, chat falls back to
its deterministic cited answer. The record is named from a slug of the first message, not from a hex
id.

**S5 — resuming an old thread.** The operator clicks a conversation in the Sessions panel. The record
is found by its id even though the id is no longer the whole filename, and the new turn is appended
to the same file — the name never changes.

## Functional Requirements

### Naming and creation

- **FR-1:** A session file MUST be named `YYYY-MM-DD-<conversation-id>-<slug>.md` under
  `<workspace>/sessions/`, where the date is the conversation's `Created` date and `<slug>` is the
  slugified conversation name. (Restores [[02-domain-model]], [[06-conversations]] §1.)
- **FR-2:** A session file MUST NOT exist until the user's first message is durably recorded.
  Reads, status probes, conversation listings and pending-plan/pending-interaction lookups MUST
  create nothing.
- **FR-3:** A session file's header (frontmatter + the `# Conversation — <name>` H1) MUST be rendered
  from `templates/template-conversation.md` by placeholder substitution. A line whose placeholder
  resolves to no value MUST be omitted entirely, so a static template can carry the app's
  conditional fields. (Constitution P7, [[21-outputs]] §3.)
- **FR-4:** The conversation's name and tags MUST come from the assistant via a `name_conversation`
  tool, resolved **within the turn already running**. The feature MUST NOT add a model round trip or
  delay the first reply. ([[006-mcp-capability-tools]].)
- **FR-5:** When the agent runtime is unavailable, does not call the tool, or supplies an unusable
  title, the name MUST fall back to a **deterministic** slug of the first user message. A name that
  slugifies to empty (emoji-only, punctuation-only, non-Latin scripts) MUST fall back to the literal
  `conversation`.
- **FR-6:** A conversation's name is fixed at the moment its file is created. The file MUST NEVER be
  renamed afterwards — a durable record's path is a stable address (P1).

### Reading and resolution

- **FR-7:** `load(workspace, conversation_id)` MUST resolve the record by scanning `sessions/` for
  `*-<conversation-id>-*.md`, never by assuming the filename equals the id. A legacy flat
  `<conversation-id>.md` MUST still load. Where several files match, the `Id:` frontmatter field is
  authoritative; resolution MUST be deterministic and MUST NOT raise (a chat turn must not die on a
  duplicate).
- **FR-8:** Frontmatter parsing MUST be case-insensitive over keys and MUST accept both the
  template's `Id` and the legacy `conversation-id`.
- **FR-9:** `list_conversations` MUST NOT depend on the filename encoding the id: it MUST parse each
  file it finds and skip any it cannot parse as a conversation.
- **FR-10:** The conversation name MUST be the title reported in `ConversationSummary` and
  `ConversationDetail`, falling back to the first user line when a record has no name (e.g. a
  pre-migration file). ([[004-assistant-sidebar]] FR-33.)

### Migration

- **FR-11:** Existing session files MUST be migrated to the FR-1 name by a one-off, **idempotent**
  operation that preserves turn bodies **byte-for-byte** and commits in each workspace's own git
  repo.

## Key Entities

| Entity | Where | Notes |
|--------|-------|-------|
| **Session record** | `<workspace>/sessions/YYYY-MM-DD-<id>-<slug>.md` | The durable conversation (P1). Header rendered from the template; turn blocks append-only. |
| **Conversation name** | the `# Conversation — <name>` H1 | Authoritative. Lives in the body, which frontmatter rewrites never touch, so it cannot be clobbered mid-conversation. The filename slug is *derived* from it. |
| **Tags** | the `Tags: [...]` frontmatter line | 1–4 short lowercase topic tags, agent-supplied. Descriptive only in this feature; no behaviour keys off them yet. |
| **`name_conversation`** | agent MCP tool | Turn-local: it records a *proposal* in the running turn's context. It touches no workspace and has no effect to undo (`EFFECTS` tier `auto`). |

## Design Decisions

- **D1 — the template is rendered, not merely documented.** Code reads
  `templates/template-conversation.md` and substitutes placeholders. The alternative (keep building
  strings in code, leave the template as prose) guarantees the two drift and makes P7 aspirational.
  A missing or unreadable template falls back to an inlined copy of its current content, so deleting
  the template degrades the header rather than breaking chat.
- **D2 — the template renders the *header* only, once.** Turn blocks are append-only (FR-7 of
  [[002-assistant-chat]]), so the template's `{{logs}}` slot marks where turns begin and is dropped;
  the body is never re-rendered. Mid-conversation frontmatter rewrites re-render only the
  frontmatter block, preserving the template's key order and capitalization.
- **D3 — "not on disk yet" is represented by `path is None`.** A single nullable field rather than a
  separate boolean, so the two cannot disagree, and every unguarded use of the path becomes a type
  error. Exactly three functions materialize a file — `append_turn`, `append_event` and the
  frontmatter rewriter — which transitively covers every `set_pending_*` / `set_sdk_session_id`
  mutator. Everything else is pure.
- **D4 — the id stays in the filename.** With the id present, lookup is an exact glob and name
  collisions are structurally impossible, so no disambiguating suffix and no uniqueness check is
  needed. The cost is a less pretty filename; the benefit is that FR-6 (never rename) and FR-7
  (resolve by id) are both cheap.
- **D5 — the name is resolved before the file, never after.** The fallback name is set before the
  agent runs; the agent's better title overwrites it after the stream and before the first
  `append_turn`. Because the only writer of the name runs before the only writer of the file, no
  rename-after-write is ever needed (FR-6), and FR-4's "no extra round trip" is structural rather
  than a promise.
- **D6 — migration is not a hard cutover.** `load` keeps a legacy `<id>.md` fallback (FR-7)
  regardless of migration, so a backup, another checkout, or a skipped script still resumes.

## Acceptance Criteria

- [x] **AC-1:** After one chat turn, the workspace's `sessions/` holds exactly one `*.md`, and its
  name matches `^\d{4}-\d{2}-\d{2}-[0-9a-f]{12}-[a-z0-9-]+\.md$`. (FR-1)
- [x] **AC-2:** A `/api/chat/status` probe plus a `/api/sessions` listing against a never-used id
  leave `sessions/` with **zero** `*.md` files; and a pending-plan/pending-interaction lookup for an
  unknown id creates nothing. (FR-2)
- [x] **AC-3:** Every frontmatter key and the H1 form present in `templates/template-conversation.md`
  appear in a freshly written record, in the template's order and capitalization; a placeholder with
  no value leaves no empty line behind. (FR-3)
- [x] **AC-4:** When the agent calls `name_conversation`, the record's filename slug and H1 derive
  from that title and its `Tags:` line from those tags — within the same turn, with no second agent
  invocation. (FR-4)
- [x] **AC-5:** With no runtime reachable (offline fallback), the slug is the slugified first user
  message; a message that slugifies to empty yields `…-conversation.md`. (FR-5)
- [x] **AC-6:** A second turn on the same conversation id appends to the same single file and does
  not rename it, even when the agent proposes a different title. (FR-6)
- [x] **AC-7:** When the assistant pauses (approval or clarification card) **before** the first turn
  is appended, exactly one file is created, named from the fallback. (FR-2/FR-5/FR-6, and see
  *Deviations*.)
- [x] **AC-8:** `load` resolves a conversation by id from the dated filename, and also loads a
  hand-written legacy `<id>.md`; two files matching one id resolve to the one whose `Id:` matches,
  without raising. (FR-7)
- [x] **AC-9:** A record written with the template's capitalized keys parses identically to one
  written with the legacy lowercase keys. (FR-8)
- [x] **AC-10:** A stray non-conversation `.md` dropped into `sessions/` is skipped by the listing,
  which still returns 200 and the real conversations. (FR-9)
- [x] **AC-11:** The Sessions panel title for a named conversation is its name, not its raw first
  message. (FR-10)
- [x] **AC-12:** Migration renames a legacy record to the FR-1 form with an unchanged turn count and
  unchanged turn text; running it a second time changes nothing. (FR-11)

## Deviations recorded during implementation

- **A paused first turn keeps the fallback name.** The assistant can raise an approval or
  clarification card *before* the turn's reply is appended, and a pending card is durable state that
  must be written — which materializes the file. At that instant the agent's title may not exist
  yet, so the record is named from the FR-5 fallback and the later title is discarded (FR-6 forbids
  renaming). This is accepted: the alternative is either a rename (breaking a durable address) or
  deferring the card (breaking spec 008), and a paused first turn is the uncommon case.

- **The fallback name is threaded to the card writers as `name_hint`.** `capabilities.create_interaction`
  and `request_approval` load their *own* `Conversation`, so without help the record a card
  materializes would have been named `conversation` — not the fallback AC-7 asks for. Rather than give
  those two functions a second naming rule, the turn's `naming` list is **seeded** with the FR-5
  fallback in `_ask_stream_impl`, with the invariant *its last entry is the best name known so far*.
  `agent.best_name()` reads that entry and passes it as `name_hint`; `convo.set_name` applies it and is
  a no-op once the file exists (FR-6). One naming source, three writers. The concierge's own card
  passes `fallback_name(run.objective)` for the same reason.

- **`load_path` returns `None` for a file that is not a conversation.** FR-9 asks the listing to skip
  unparseable files, but the reader parsed anything: a human's `sessions/notes.md` listed as an empty
  conversation whose id was `notes`. A record is now recognised by carrying a frontmatter id **or** at
  least one turn block — without either there is nothing to resume.
