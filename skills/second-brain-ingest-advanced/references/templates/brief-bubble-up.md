# Worker brief — phase {{PHASE_ID}}, lane `{{LANE_ID}}` (BUBBLE UP)

The atomic pages from the previous phase exist and passed the link and scope gates. Your job is to
build **coarser-grained** pages (entity, synthesis, reference) from them: group, rank and connect,
without copying them out again.

**Vault dir:** {{VAULT}}  ·  **Date:** {{DATE}}  ·  **Target system:** {{TARGET_SYSTEM}}

## 1. Inputs
Build from the wiki pages, not from raw sources. Open a raw source only to verify a number.
- Atomic pages to read (slugs from earlier lanes):
{{SIBLING_SLUGS}}
- Raw sources (verification only):
{{SOURCES}}
- Conventions: `docs/wiki-schema*.md`, `docs/wiki-architecture*.md`. Use an existing page in `wiki/synthesis/` as the format model.

## 2. Your contract
**Create:**
{{CREATES}}

**You may update (append-only, e.g. a "Bubbles up to" line in Related):**
{{UPDATES}}

**Write scope:**
{{WRITE_SCOPE}}

**Never touch:**
{{FORBIDDEN}}

## 3. Lane instructions
{{INSTRUCTIONS}}

## 4. Bubble-up rules
- **BLUF first:** the first 2–3 lines state the conclusion.
- **Every claim cites an atomic page:** each number or claim carries a `[[wikilink]]` to the atomic page that holds it.
  If no atomic page holds it, do not state it, or mark it `[no data in vault]`.
- **Group, don't list:** cluster the atomic pages under 3–6 themes, each with a 1–2 line thesis and a table
  (atomic page → where it applies → outcome).
- **Gaps section:** end with what the evidence does not show.
- **Reference pages** (pages that later work will read, such as an evidence map) need stable section headings,
  so a downstream brief can say "read section X".

## 5. Hand-back (required)
Write `{{MANIFEST_PATH}}` with the same schema as phase 1:
`{"lane", "created": [{path, portal_section, hook}], "updated": [{path, what}], "gaps": []}`.
Reply in at most 15 lines. Do not stage or commit.
