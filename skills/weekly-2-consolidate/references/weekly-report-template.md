# Weekly Report Template

Structure and fill instructions for the Slack-ready consolidated weekly report
(`wiki/projects/_weekly_/<date>-consolidated.md`).

This file owns the **output structure and formatting mechanics**. The editorial
judgment — what to cut, how to rewrite for a wider audience, what qualifies as a
highlight, honest status — lives in `SKILL.md`. Apply that judgment first, then pour
the survivors into this template.

Guidelines :

- Content should quote & explain how this is worth sharing (ex: Highlights or Lowlights should describe impact that reach end-users or significantly domain teams - gain or lose team member > hours)

Variable :

- `{Human Date}` = capitalized month + ordinal day, **no year**: `May 15th`,
  `May 22nd`, `June 5th`, `July 3rd`.
- **Health status** (`{:health:}`): `:large_green_circle:` (on
  track), `:large_yellow_circle:` (some blockers), `:red_circle:` (blocked).
- **Task status markers:** `[:todo_new:]`, `[:work_in_progress:]`, `[:done:]`,
  `[:blocked:]`. Keep the `[:emoji:]` text form — Slack auto-renders it.

---

## The template

The report is pasted into Slack, so it uses **plain bold project names (NOT `[[wiki links]]`)**
and a **tightly-packed layout**: NO blank line between a `**Section**` label and its
first bullet, and a **trailing double-space** (`·· ` shown here as the invisible `⎵⎵`)
after the header line and after each `**Section**` label so Slack renders a clean
line break. The `⎵⎵` below marks where two literal trailing spaces go — do not print
the symbol.

```markdown
**[ Tech Platform - {Product A} {:emojiA:} / {Product B} {:emojiB:} ]** Week of {Human Date}⎵⎵
⎵⎵
**Highlights / Lowlights**⎵⎵
- {:tada-animated:} {Big win — names who benefits}
- {:bomb:} {Issue impacting end users/teams and IF resolved}
⎵⎵
**Key projects**⎵⎵
- **{:health:}** {Display Name} **:date:** {Target}
    - [:done:] {One specific shipped outcome}
    - [:work_in_progress:] {One specific in-flight outcome}
- **{:health:}** {Display Name} **:date:** {Target} :checked:
    - [:done:] {One specific shipped outcome}
⎵⎵
**Eng Excellence**⎵⎵
- **{:health:}** Support / BAU load - {X}%
    - {Incident / notable help — combine related items with ;}
    - {Another support line}
```

---

## How to fill it correctly

### Header line

- **No YAML frontmatter.** The file starts with the header line.
- Name the **actual contributing teams/products**, not a generic umbrella. List
  each product that reported this week.
- **Capitalize the month** (`July 10th`, not `july 10th`) and use no year.
- **Only one product reported?** Name just that team and drop the missing product's
  half of the header.

### Slack layout / spacing (apply to the whole file)

The final report is pasted straight into Slack. Match this layout exactly:

- **Trailing double-space** (two literal spaces) after the header line and after
  each `**Section**` label — this is how Slack renders a line break. Also add one
  blank spacer line (itself two trailing spaces) between sections.
- **NO blank line** between a `**Section**` label and its first bullet, and none
  between bullets. The block under each section is tightly packed.
- Do not use `##` headers; sections are bold markdown labels only.

### Section labels

Bold markdown, in this exact order — **not** h2 (`##`) headers:
`**Highlights / Lowlights**`, `**Key projects**`, `**Eng Excellence**`.

### Highlights / Lowlights

- Filter only topics with significant end-user or domain-team impact (> hours saved/lost).
- **Promote quantified shipped wins.** Before settling the highlights, scan the
  surviving `[:done:]` project lines for an outcome that (a) shipped and (b) carries
  a number or a named beneficiary — a latency/throughput improvement (`P99 >30s → <1s`),
  a production cutover, a team adopting a platform. Lift the strongest 1-2 of these
  **up** into a highlight, naming who benefits. A strong metric buried in a project
  line is the most common missed highlight.
- Emoji: `:tada-animated:` (preferred) or `:tada:` for wins; `:bomb:` /
  `:rotating_light:` for resolved issues.
- Aim for **0-3 highlights** and **0-1 lowlights**.
- **N/A rule:** Write `- N/A` **ONLY** when there are zero highlights AND zero
  lowlights. If you have any lowlight, list it without N/A — the section is
  "Highlights / Lowlights", not "Highlights then Lowlights".
- **Lowlights are resolution-focused:** Frame around the **fix**, not the problem.
  Write `Resolved P3 incident — applied filter fix` not `P3 incident — noisy query`.

### Key projects

Each project is one bullet, its task lines indented beneath.

- **Health status** (`{:health:}`), **bold-wrapped**. Take the circle from the
  **project page `Status`** (In Progress / On Track → green, At Risk / blockers →
  yellow, Blocked → red), **not** from counting open task markers. This is an
  audience-facing status: **default to green** for a project that is progressing, and
  reserve yellow/red for a real, worth-communicating blocker. Do **not** downgrade to
  yellow just because a line is `[:work_in_progress:]` or `[:todo_new:]`.
- **Display name — PLAIN BOLD, NO wiki link.** Write the **plain alias** from
  portal.md in the health-circle bold run (e.g. `**:large_green_circle:** User service`).
  Do **NOT** emit `[[project-key|…]]` — the report is pasted into
  Slack, which cannot render wiki links. Strip any `Project:` prefix, `(P1)` marker,
  and internal suffixes that add nothing (`… with user token`).
- **`**:date:**`** (bold) follows the name, then the plain target date. **Omit
  `:date:`** entirely if portal.md has no target — never invent one.
- **`:checked:`** goes after the name (and after the date if present) when the
  project was marked Complete in the Phase-1 wiki files. A completed line is either
  `**:large_green_circle:** Events :checked:` (no date) or
  `**:large_green_circle:** Cluster migration **:date:** Mid June :checked:`.
- **Task status markers:** Keep the `[:emoji:]` text form — Slack auto-renders it.
  Never use raw `![:done:](url)` HTML emoji URLs.
- **Verb-first formulation:** Each task line starts with a past-tense action verb
  immediately after the status marker: `[:done:] Migrated…`, `[:done:] Shipped…`,
  `[:done:] Resolved…`, `[:work_in_progress:] Developing…`. Avoid noun phrases.
- **Emphasis:** Bold the **key term** (team name, feature name, system affected) so
  lines skim well: `Migrated **User & Account** to production`, `Shipped **business-info**
  category`. Use `~~strikethrough~~` for deprecated systems (`migrated from
  ~~old-service~~ to new-service`).

### Merge related projects under one flagship (do this before ordering)

The audience thinks in **flagships**, not in the internal sub-project split. Before
listing, collapse sibling / parent-child efforts into the single name the audience
recognizes:

- **Follow the portal hierarchy.** In `portal.md`, indented projects are children of
  the project above them. When a parent and its child (or two siblings) both have
  updates this week, report them as **one** bullet under the most externally-recognizable
  name — usually the flagship child. Example: `User service` (parent) security
  work folds **into** `Secured authentication`, etc.
- **Honor the `Report Under:` clue.** If a project page's `## Weekly Signal` block
  sets `Report Under: <alias>`, roll its surviving line into that flagship's bullet
  instead of giving it its own bullet.
- Keep the **date and health** of the flagship you merge into.

### Ordering (never interlace products)

List **all Product A projects first**, then **all Product B projects**. Within each
product, order by:
1. **Px projects** (marked `(Px)` in the portal description in order) — regardless of status
2. Completed-this-week / `:checked:` milestones
3. In-progress flagship projects (migrations, big launches)
4. Smaller / steady-state projects

**Priority markers are for ordering ONLY** — never print `(P1)`/`(P2)`/`(P3)`/`(P4)` in the
report; strip them if they appear in the portal description.

### Eng Excellence

- One BAU **percentage** with a health status for the whole team (bare `{:health:}` is fine here, no
  bold). If the wiki file gives a range like `10-15%`, use the **midpoint**. Above 30% is `:large_yellow_circle:`, above 45% is `:red_circle:`.
- **Combine team percentages:** If Product A reports 5% and Product B reports 15%, report
  a single combined number (`~10%` or weighted average) — not separate breakdowns.
- **Plain text** support items — no task status markers.
- **Combine** related items on one line with `;`. Aim for **2-3 bullets total** — do
  not list one bullet per ticket. Drop routine oncall noise; keep incidents and
  notable cross-team help.
- **Resolution-focused:** Frame incidents around what was fixed, not the investigation.
  Write `CPU saturation mitigated` not `Investigated CPU saturation`.
