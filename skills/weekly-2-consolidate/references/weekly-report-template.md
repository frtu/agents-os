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

```markdown
**[ Tech Platform - {Product A}** **{:emojiA:}** **/ {Product B}** **{:emojiB:}** **]** Week of {Human Date}

**Highlights / Lowlights**
- {:tada-animated:} {Big win — names who benefits}
- {:bomb:} {Issue impacting end users/teams and IF resolved}

**Key projects**
- **{:health:}** [[{project-key}|{Display Name}]] **:date:** {Target}
    - [:work_in_progress:] {One specific in-flight outcome}
    - [:todo_new:] {Next step}
- **{:health:}** [[{project-key}|{Display Name}]] **:date:** {Target}
    - [:done:] {One specific shipped outcome}
    - [:work_in_progress:] {One specific in-flight outcome}
- **{:health:}** [[{project-key}|{Display Name}]] **:date:** {Target} :checked:
    - [:done:] {One specific shipped outcome}

**Eng Excellence**
- {:health:} Support / BAU load - {X}%
    - {Incident / notable help — combine related items with ;}
    - {Another support line}
```

---

## How to fill it correctly

### Header line

- **No YAML frontmatter.** The file starts with the header line.
- Name the **actual contributing teams/products**, not a generic umbrella. List
  each product that reported this week.
- **Bold-wrap each emoji** separately (renders cleaner in Slack), as shown.
- Put a **trailing double-space** after the header line and after each `**Section**`
  label so Slack renders a clean line break when pasted.
- **Only one product reported?** Name just that team and drop the missing product's
  half of the header.

### Section labels

Bold markdown, in this exact order — **not** h2 (`##`) headers:
`**Highlights / Lowlights**`, `**Key projects**`, `**Eng Excellence**`.

### Highlights / Lowlights

- Filter only topic significantly big win or issue : usually impacting end users or domain teams (gain or lose > hours).
- Emoji: `:tada-animated:` (preferred) or `:tada:` for wins; `:bomb:` /
  `:rotating_light:` for issues.
- Aim for **0-3 items**. If nothing qualifies (see SKILL highlight-admission rules),
  write a single line `- N/A`. That is normal, not a failure.

### Key projects

Each project is one bullet, its task lines indented beneath.

- **Health status** (`{:health:}`), **bold-wrapped**.
- **Drill-down link:** `[[{project-key}|{Display Name}]]`. Keep the wiki link from
  the Phase-1 page / portal so a reviewer can click through in Obsidian. The
  `{Display Name}` is the **plain alias** from portal.md — no `Project:` prefix, no
  `(P1)` marker, no internal suffixes that add nothing (`… with IAM`).
- **`**:date:**`** (bold) follows the link, then the plain target date. **Omit
  `:date:`** entirely if portal.md has no target — never invent one.
- **`:checked:`** goes after the name (and after the date if present) when the
  project was marked Complete in the Phase-1 wiki files. A completed line is either
  `**:large_green_circle:** [[project-events|Events]] :checked:` (no date) or
  `**:large_green_circle:** [[project-x|Cluster migration]] **:date:** Mid June :checked:`.
- **Task status markers:** : Keep the `[:emoji:]` text form — Slack auto-renders it. Never use
  raw `![:done:](url)` HTML emoji URLs.
- **Emphasis:** bold the key term in a line so it skims (`Added **business-profile**
  category`). Use `~~strikethrough~~` for a system being deprecated/migrated away
  from (`migrated from ~~name-screening-service~~ to search-service`).

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
- **Plain text** support items — no task status markers.
- **Combine** related items on one line with `;`. Aim for **2-3 bullets total** — do
  not list one bullet per ticket. Drop routine oncall noise; keep incidents and
  notable cross-team help.
