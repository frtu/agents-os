# Team Cases — registry

Team-specific context and past retros. The template (`../templates/retrospective-report.md`) stays generic; everything specific to one team lives here. **Load only one case file** — the team's own, or the one worked example that matches the input — never all of them up front.

| Case | Team                                        | Format                               | Pattern it illustrates                                                                  | Retros captured        | File                   |
| ---- | ------------------------------------------- | ------------------------------------ | --------------------------------------------------------------------------------------- | ---------------------- | ---------------------- |
| A    | Checkout Product Squad                      | Went well / To improve / Actions     | Thin sticky board, actions restate problems; **full Produce-mode output**               | 2026-06-12             | `a-product-squad.md`   |
| B    | UX Research & Design                        | Goal-framed (goal + 3 columns)       | Retro called for a decision that the report never answers                                | 2026-03-06             | `b-ux-research.md`     |
| C    | Platform Eng. — cloud migration             | Sailboat (Island/Wind/Anchors/Rocks) | Metaphor mapping; risks with no home → *Risks to watch*; top-voted item is a leadership decision | 2026-07-30        | `c-cloud-migration.md` |
| D    | Mobile App Team                             | WRAP (Wishes/Risks/Appreciations/Puzzles) | Future-only board, no evidence; misfiled stickies; puzzle = decision request       | 2026-05-08             | `d-mobile-app.md`      |
| E    | Customer Conference Programme (cross-functional) | 4Ls (Liked/Learned/Lacked/Longed for) | One-off event retro; luck as a win; many small items, one upstream cause; long carry-over gap | 2026-09-11   | `e-customer-event.md`  |

All cases are **synthetic**, generified to industry-standard systems and roles (no real teams, companies, vendors or people). Replace or add real team cases alongside them.

**Two ways to use a case:**

- **Team case** — the user's team has a file here: load it for team context and the last **Carry-over** list.
- **Worked example** — the team is new, or the input uses an unfamiliar format: load the **one** case whose *Format* or *Pattern* matches, and follow how it maps, reviews and produces. Don't import its team context.

Each case file carries:

- **Frontmatter** — `case`, `team`, `format`, `pattern`, `sub-areas`, `retros` (list of dates), `source`.
- **Team context** — sub-areas, how to group items and themes, recurring themes, key metrics to ask for.
- **Format mapping used** — only when the board isn't already in the template's shape (see `../templates/retro-formats.md`).
- **One section per retro** (`## Retro YYYY-MM-DD`, newest last) — the captured content (raw or mapped to the template), the **Review findings**, optionally the produced/fixed summary and a **Proposed action table**, and the **Carry-over for next retro** (actions to check next time).

## Adding to the registry

**Same team, new retro:**
1. Append a `## Retro YYYY-MM-DD` section to the team's file.
2. Start its review by checking the previous section's **Carry-over** list (template §3).
3. Update the team context if sub-areas, themes, or metrics changed.
4. Add the date to the frontmatter `retros` list and to the table row above.

**New team:**
1. Create `{next-letter}-{team-slug}.md` in this folder, following the structure above.
2. Add one row to the table above, with its format and the pattern it illustrates.
3. Anonymise: name systems by category ("LLM gateway", "lakehouse", "event bus"), people by role, and never copy company-internal names, links or dashboards.

Keep team specifics (names of systems, metrics, owners) **here**, never in the template or `SKILL.md`. If a review finding recurs across several teams, promote it to a generic rule in the template instead.
