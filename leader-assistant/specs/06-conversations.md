---
id: 202608132112-06
title: Conversation Capture & Dreaming
spec: 06-conversations
layer: moc
status: draft
lifecycle: draft
Category: spec
Tags: [conversations, sessions, dreaming, promotion-pipeline]
traceability:
  readme: ["§9 Conversation Capture", "§12 Knowledge Operations"]
  references: ["_references_/10-internal-storage/wiki-schema.md#sessions-directory", "_references_/10-internal-storage/wiki-schema.md#dreaming-daily-session-compaction"]
related:
  - "[[03-workspace]]"
  - "[[04-knowledge-ingestion]]"
  - "[[05-zettelkasten]]"
  - "[[16-workflows]]"
Created: 2026-08-13
Last Updated: 2026-08-13
---

# Conversation Capture & Dreaming

Every application conversation is captured automatically. Conversations are an interaction mechanism (volatile/operational) **and** a knowledge-patch candidate that is filtered before entering durable knowledge.

## 1. Sessions (short-term memory)

Conversation threads are stored under `sessions/` (e.g. `sessions/2026-08-12-a1b2c3d4e5f6-project-spec.md`). They hold: instructions for specific tasks, human decisions/judgments (upvotes/downvotes), and complements/corrections that could improve knowledge maturity. Sessions are **ephemeral operational capture**, not durable knowledge, and are **not** part of the wiki.

A thread's file is created **lazily** — only once the user's first message is durably recorded, never by a status probe or a listing — and its header is rendered from the human-owned `templates/template-conversation.md`. The name is chosen during the turn that is already running, and the file is never renamed afterwards. See [[012-conversation-naming]].

## 2. Two-Stage Knowledge Promotion

```text
vault/raw/{provenance}/              (immutable source)
     │
     ▼
Conversation
     │
     ▼
sessions/                      (operational capture)
     │
     ▼  DREAMING (daily)
     │
vault/wiki/sources/_daily_/          (daily digest, references sessions)
     │
     ▼  INGEST
     │
vault/wiki/sources/{provenance}/{source}.md   (source summary — preserves provenance)
     │
     ▼
vault/wiki/{categories}              (standalone knowledge — no session refs)
```

**Key rule**: session references exist *only* in daily digests; source summaries preserve provenance by mirroring `vault/raw/`; category pages reference source summaries. Durable knowledge stays clean while the full provenance chain is preserved.

## 3. Dreaming Operation (daily / on demand)

1. Scan all sessions from the current day.
2. Extract: human decisions (upvotes, downvotes, corrections, confirmations); knowledge complements (new info, refinements, edge cases); important context (reasoning, constraints).
3. Write `vault/wiki/sources/_daily_/YYYY-MM-DD.md` with frontmatter (`Category: daily-digest`, `Date`, `Sessions: [[...]]`) and sections: **Key Decisions**, **Knowledge Candidates** (each with Type = correction|complement|new-concept, Target = existing/new page, Content = distilled knowledge).
4. Append `## [YYYY-MM-DD] dreaming | Daily digest` to `vault/wiki/log.md`.

The daily digest is the **input to standard ingestion** ([[04-knowledge-ingestion]]).

## 4. Distinction to Preserve

Conversation capture is about immediate/adhoc operational resolution — not to be confused with processed knowledge. It may contain judgments (upvote/downvote) or complements that should be *referenced* into knowledge, not copied verbatim.

## 5. Acceptance Criteria

- AC1: Every conversation is persisted to `sessions/` automatically.
- AC2: Dreaming produces one daily digest per active day, referencing its source sessions.
- AC3: Final wiki category pages contain no direct session/daily-digest references.
- AC4: Human upvotes/downvotes in sessions influence concept `status`/corrections during ingestion.
- AC5: Each dreaming pass appends exactly one `dreaming` log entry.
