# Worker brief — phase {{PHASE_ID}}, lane `{{LANE_ID}}` (ATOMIC pages)

You are one of several parallel writers in an Obsidian LLM-wiki ingest. Other workers write other
folders at the same time. You are safe only if you stay inside your lane.

**Vault dir:** {{VAULT}}  ·  **Date:** {{DATE}}  ·  **Target system:** {{TARGET_SYSTEM}}

## 1. Read first (conventions)
- `docs/wiki-schema*.md` and `docs/wiki-architecture*.md` in the vault (extension files win on conflict)
- One or two existing pages in your write scope, as format models
- `{{INVENTORY_PATH}}` — every slug that already exists. Update an existing page rather than
  creating a near-duplicate.

## 2. Sources (read fully; never modify)
{{SOURCES}}

## 3. Your contract
**Create exactly these pages (slugs are fixed; other lanes already link to them):**
{{CREATES}}

**You may update these existing files:**
{{UPDATES}}

**Write scope: you may create or modify files only under:**
{{WRITE_SCOPE}}

**Never touch (owned by the orchestrator or another lane):**
{{FORBIDDEN}}

**Slugs created by other lanes. Link to them exactly as written, even if the page does not exist yet:**
{{SIBLING_SLUGS}}

## 4. Lane instructions
{{INSTRUCTIONS}}

## 5. Page rules
- One concept per page. Frontmatter per schema, `Created`/`Last Updated` = {{DATE}}, `Source links` → the run's source pages.
- Copy numbers exactly as the source states them. Never derive or invent a number. Mark gaps `[no data in vault]`.
  If two sources disagree, keep both and add a `> **Caveat:**` line.
- Preserve existing content when updating. Add a dated "Field notes" section or append to Related.
- Wikilinks: `[[slug]]` or `[[slug|Display]]`; inside tables escape the pipe `[[slug\|Display]]`.
  Never write a vault path inside a link.
- Before finishing, check that every same-vault link you wrote points at an existing page or at a sibling slug above.

## 6. Hand-back (required)
Write the JSON manifest to `{{MANIFEST_PATH}}`:

```json
{"lane": "{{LANE_ID}}",
 "created": [{"path": "wiki/<folder>/<slug>.md", "portal_section": "## <Top> > ### <Sub>", "hook": "<one line, under 120 chars>"}],
 "updated": [{"path": "wiki/<folder>/<slug>.md", "what": "<what was added>"}],
 "gaps": ["<contradiction or missing data, one per line>"]}
```

Then reply with at most 15 lines: files created/updated, and anything the orchestrator must decide.
Do not stage or commit.
