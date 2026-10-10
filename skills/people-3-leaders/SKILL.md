---
name: people-3-leaders
description: >
  Create or update a person's wiki pages from whatever sources are in the
  current execution context (raw notes, transcripts, Slack exports, meeting
  threads, other vaults). Extracts a template from existing member pages,
  fills only what the evidence supports, and supports a two-tier
  canonical-profile + workspace-scoped-ref pattern. Step 3 of people-ingest,
  for leaders, peers and stakeholders (not assessed against the ladder). Use
  when the user says "create a profile for {name}", "add {name} to the wiki",
  "new member page", or asks to fill a people page from a source at hand.
  Direct reports mapped to role/skills go to people-2-member-reports.
allowed-tools: Bash Read Write Edit Glob Grep
risk-level: low
---

# People 3 — Leaders

Create a member page (and, in multi-vault setups, its workspace-scoped
companion) for one named person, filling from evidence available in the
current execution context — the file the user just read, a raw source in the
vault, or pages already in a sibling vault.

This skill is **template-first**: it never invents a page structure. The
template is *extracted from the vault's own member pages at run time*, so it
always matches that vault's current conventions (which evolve vault by
vault).

Core vault named : `{core-people}`=`management`

## When to use

Leaders, peers, stakeholders — people you profile, not assess. For a **direct report**
mapped against role, level and skills, use `/people-2-member-reports` instead.

- "Create a profile for {Name}" / "add {Name} to people"
- A source thread mentions a new person prominently and the user wants their page
- The user asks for a `{name}-ref-…` scoped page in a non-canonical workspace

## Inputs to gather (step 1)

Collect all of these before writing anything:

1. **The person**: full name, slug, any aliases (source thread, user, portal).
2. **Evidence in context**: files already read this session, `vault/raw/**`
   matches for the name, and recently changed/added files in `vault/raw/`.
3. **Canonical vs scoped**:
   - Search every workspace vault for an existing page for this person:
     `find ~/…/Workspaces/*/vault/wiki/people/members -iname "*{slug}*"` and
     grep the portals. A `{core-people}`-style vault holding full leadership
     profiles is the **canonical** home; project/topical vaults hold scoped
     `-ref` pages (see "Two-tier pattern").
   - If the user names the target vault explicitly, honor that exactly.
4. **The template**: extract from existing member pages (next section).

## Template extraction (step 2)

**Never hardcode a template.** Build it from the target vault's member pages:

```bash
ls vault/wiki/people/members/                    # inventory
```

Read 2–3 existing member pages that best match the person's kind
(leader-with-transcript-history → richest page; minimal source → simplest
page). From them, derive:

- **Frontmatter keys** in use: `Category`, `Aliases`, `Tags`, `Source links`,
  `Created`, `Last Updated` (accept key variants like `Sources:` — follow the
  *majority convention of that vault*).
- **Section skeleton**: role line under the title, site line, profile
  paragraph, role/facts table, evidence sections, `## Related`.
- **Naming conventions**: filename slug (kebab-case of display name), display
  title form, alias list contents, tag vocabulary.
- **Wikilink style**: short `[[fred-tu]]` vs full-path cross-vault
  `[[Workspaces/…/members/fred-tu|Fred Tu]]` forms — copy exactly what the
  vault already uses.

State the extracted skeleton to the user in one line before writing
(e.g. "template from eric-sun.md: frontmatter / role+site line / Current
Profile / Role table / evidence sections / Related").

## Fill rule: evidence-bounded (step 3)

Fill the template **only with facts present in the gathered evidence**. For
each section:

- **Have evidence** → write it, citing the source page/wikilink.
- **No evidence, field is structural** (name, role line if known, dates,
  source links) → fill with what is known; leave unknowns blank or omit the
  row — do not guess.
- **No evidence, section is content** → omit the section entirely, or create
  it with an explicit gap marker:

  ```markdown
  ## Leadership Focus

  > No evidence in current sources. Fill from the next 1:1 transcript.
  ```

- **Inference beyond the source** (RACI, ownership, org placement) → allowed
  only if labelled, e.g. "*inferred*, not read from labels — see the source
  page's warning".

**Evidence hygiene** (carried over from `second-brain-ingest` step 1b):
- Do not trust speaker labels in transcripts; attribute to the meeting when
  diarization is unreliable.
- Cross-check roles — "X deals with Y" does not make Y X's report.
- Unresolved names stay plain text; never mint a `[[wikilink]]` for a person
  or concept page that does not exist, unless it is a deliberate cross-vault
  link per the two-tier pattern.
- End the page (or the risky section) with a short **Note on evidence** when
  attribution was hard: what source, what is uncertain, what would settle it.

**Link to the people structure — only when relevant.** If the vault has
`wiki/people/roles/` or `competencies/` (built by `/people-1-structure`) and the
evidence states the person's ladder level or shows a named competency, link it
using the formats in `people-ingest/references/people-schema.md`
(`[[role-{track}-{level}|…]]`, `[[{skill}#…Depth Progression|…]]`). Don't build a
competency table or assess depth — that is `/people-2-member-reports`' job.

## Two-tier pattern: canonical profile + scoped ref (step 4)

In a multi-workspace setup (one `{core-people}` vault with full profiles, plus
topic vaults), a person gets **two pages**:

| Tier      | Home                                                            | Scope                                                                               | Links                                                                                                              |
| --------- | --------------------------------------------------------------- | ----------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------ |
| Canonical | `{core-people}/vault/wiki/people/members/{slug}.md`             | Full profile: role, reporting line, leadership practices, career record             | Points forward to every scoped ref                                                                                 |
| Scoped    | `{topic-vault}/vault/wiki/people/members/{slug}-ref-{topic}.md` | Only the person's role **in that workspace's topic**; explicitly disclaims the rest | Points back to canonical: "Reference to [[…]] in `{core-people}` workspace. This page captures the {topic} view only" |

Rules:

- **Create canonical first** (when evidence allows), then the scoped page;
  both reference each other.
- **Never duplicate** canonical content into a ref page — one-line pointer
  summary, then topic-only facts.
- If canonical evidence is thin, create only the scoped page and say so.
- Frontmatter of a scoped page: alias the bare slug so Obsidian resolves
  `[[{slug}]]` sensibly inside that vault; include a `Source links` entry for
  the canonical page as a full-path wikilink.
- Each vault's `portal.md` gets only its own page.

## Sources & plumbing (step 5)

- **Source summary page.** If the evidence is a raw file that has no
  `wiki/sources/source-{slug}.md` yet, create a factual summary page (title,
  metadata, key claims, structured summary) — a ref page citing
  `[[source-…]]` must not dangle within the same vault.
- **Portal.** One line per new page under the right category
  (`### Members`, `## Sources`), ≤120 chars:
  `- [[{slug}|{Name}]] — {role}, {one-line relevance to the vault}`
- **Log.** Append-only entry: `## [YYYY-MM-DD] create | Member page: {Name}`
  with what/where/why and cross-vault pointer.
- **Frontmatter dates**: `Created` = `Last Updated` = today.

## Validation checklist (step 6)

Before finishing, verify:

- [ ] Template used matches the vault's existing member pages (not a generic guess)
- [ ] Every factual claim traces to a cited source in the page
- [ ] No unfilled placeholder text like `{Name}` or `TBD` left in prose
- [ ] No guessed facts — unknowns are omitted or explicitly gap-marked
- [ ] All same-vault wikilinks resolve (`find wiki -name "{slug}.md"` per link);
      cross-vault links may dangle
- [ ] Wikilinks inside tables use `\|` escaping
- [ ] Canonical ↔ ref pages cross-reference each other (two-tier case)
- [ ] `portal.md` and `log.md` updated in every touched vault (append-only log)
- [ ] Files staged via `/change-management-1-stage` if the user wants them captured

## Report (step 7)

Tell the user: template source used · pages created/updated per vault ·
evidence used and what was deliberately left blank · dangling or
plain-text-only names awaiting confirmation.

## Anti-patterns

- **Inventing structure** — a hardcoded "modern template" that drifts from the vault.
- **Biography padding** — filling sections from plausible general knowledge
  instead of the evidence at hand.
- **Duplicating canonical into ref** — ref pages rot when the canonical changes.
- **Committing roles from context** — "heads Risk engineering" is a claim the
  source must make, not one the surrounding conversation implies.
- **Skipping the source page** — a ref page citing a `[[source-…]]` that was
  never created breaks the vault's citation chain.
