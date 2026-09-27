# Worked cases — registry

Synthetic, anonymised retros that show how a board format maps onto the template, what a review finds, and what the fixed output looks like. The template (`../templates/retrospective-report.md`) stays generic. **A real team's history does not live here** — it lives in the vault's retrospective folder (prep files and past reports), which `retrospective-1-gather` reads for carry-over. **Load at most one case**, the one whose format or pattern matches the input.

| Case | Team                                        | Format                               | Pattern it illustrates                                                                  | Retros captured        | File                   |
| ---- | ------------------------------------------- | ------------------------------------ | --------------------------------------------------------------------------------------- | ---------------------- | ---------------------- |
| A    | Checkout Product Squad                      | Went well / To improve / Actions     | Thin sticky board, actions restate problems; **full Produce-mode output**               | 2026-06-12             | `a-product-squad.md`   |
| B    | UX Research & Design                        | Goal-framed (goal + 3 columns)       | Retro called for a decision that the report never answers                                | 2026-03-06             | `b-ux-research.md`     |
| C    | Platform Eng. — cloud migration             | Sailboat (Island/Wind/Anchors/Rocks) | Metaphor mapping; risks with no home → *Risks to watch*; top-voted item is a leadership decision | 2026-07-30        | `c-cloud-migration.md` |
| D    | Mobile App Team                             | WRAP (Wishes/Risks/Appreciations/Puzzles) | Future-only board, no evidence; misfiled stickies; puzzle = decision request       | 2026-05-08             | `d-mobile-app.md`      |
| E    | Customer Conference Programme (cross-functional) | 4Ls (Liked/Learned/Lacked/Longed for) | One-off event retro; luck as a win; many small items, one upstream cause; long carry-over gap | 2026-09-11   | `e-customer-event.md`  |

All cases are **synthetic**, generified to industry-standard systems and roles (no real teams, companies, vendors or people). Real team retros stay in the vault, not here.

Use a case as a **worked example** when the input uses an unfamiliar format or shows a known failure pattern: follow how it maps, reviews and produces. Don't import its team context.

Each case file carries:

- **Frontmatter** — `case`, `team`, `format`, `pattern`, `sub-areas`, `retros` (list of dates), `source`.
- **Team context** — sub-areas, how to group items and themes, recurring themes, key metrics to ask for.
- **Format mapping used** — only when the board isn't already in the template's shape (see `../templates/retro-formats.md`).
- **One section per retro** (`## Retro YYYY-MM-DD`, newest last) — the captured content (raw or mapped to the template), the **Review findings**, optionally the produced/fixed summary and a **Proposed action table**, and the **Carry-over for next retro** (actions to check next time).

## Adding to the registry

1. Only add a case for a **new format or a new failure pattern** — not for every real retro (those stay in the vault).
2. Create `{next-letter}-{slug}.md` in this folder, following the structure above.
3. Add one row to the table above, with its format and the pattern it illustrates.
4. Anonymise: name systems by category ("LLM gateway", "lakehouse", "event bus"), people by role, and never copy company-internal names, links or dashboards.

If a review finding recurs across several cases, promote it to a generic rule in the template.
