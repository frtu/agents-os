# Retro prep file — template

Structure of `{Retro Folder}/{date}-{team}-retrospective.md`, the **pre-meeting dossier**. Step 1 fills §1–§7; step 2 replaces the `## Facilitation guide` placeholder; step 3 links the report and sets `status: reported`.

The dossier is for the **facilitator**. It collects what the team already said and what it committed to, so the meeting spends its time on insight and decisions rather than re-listing problems.

---

## Skeleton

```markdown
---
Category: projects
Tags: [retrospective, {team}]
team: {team}
date: {YYYY-MM-DD}            # meeting date
cycle: {YYYY-MM-DD} → {YYYY-MM-DD}
status: gathered              # gathered → questions-ready → reported
previous: "[[{prev-date}-{team}-retrospective-report]]"   # or "none"
report: ""                    # set by step 3
Source links:
  - {raw files used}
Created: {date}
Last Updated: {date}
---

# Retro prep — {Team} — {date}

**Cycle:** {start} → {end} · **Facilitator:** {name or [need input]} · **Format:** decided in step 2
**Previous retro:** [[{prev report}]] or *first retro on record*

## 1. Carry-over from last retro
## 2. Signals this cycle
## 3. Team-raised problems
## 4. Wins raised
## 5. Open questions
## 6. Provisional themes
## 7. Gaps to fill before the meeting

## Facilitation guide

status: pending — run `/retrospective-2-questions`
```

---

## Section guidance

Each section: **insight it must deliver**, **format**, **questions to answer** (same pattern as the report template).

### 1. Carry-over from last retro

- **Insight:** what the team committed to, so the meeting opens by closing the loop.
- **Format:**

  | # | Action (from {prev date}) | Owner | Due | Success signal | Evidence found pre-meeting | Status to confirm |
  |---|---|---|---|---|---|---|
  | 1 | … | … | … | … | link / number / "none found" | Done? / In progress? / Dropped? |

  Then two short lists: **Risks to watch** carried from last time (with their early signal — has it moved?) and **Decisions left open** (puzzles, "who decides by when" items).
- **Questions to answer:**
  - Is there evidence already (ticket closed, metric moved) so the meeting only confirms?
  - Which pains from last time have no action at all? List them — they tend to come back.
  - Which actions had no owner last time? Those are the likeliest to have slipped.
- **Source:** the previous `*-{team}-retrospective-report.md` — its *Action items*, *Risks to watch* and *Carry-over for next retro*. If only a prep file exists (no report), use its questions and say so.

### 2. Signals this cycle

- **Insight:** the numbers the discussion should be anchored on.
- **Format:** one table — metric · this cycle · previous · source. Only metrics that exist; no invented ones. Missing ones go to §7.
- **Questions to answer:** did the metric each previous action targeted move? What changed most this cycle (incidents, delivery, cost, load)?

### 3. Team-raised problems

- **Insight:** what the team is already saying hurts — before anyone is in the room.
- **Format:** grouped by provisional theme. Each bullet: the problem in the team's words (quoted or close) · how many people raised it · source (survey, async board, 1:1, channel) · *recurring?* flag if it matches a past pain.
- **Rules:** keep every item (nothing dropped silently); **no attribution** unless the input was already public; blameless — systems and processes, not people.

### 4. Wins raised

- **Insight:** what to protect, with the evidence already known.
- **Format:** bullets, each with evidence or `[need input]`.

### 5. Open questions

- **Insight:** what the meeting must answer or decide.
- **Format:** numbered list. Tag each: *from last retro* / *new* / *decision request* (needs an owner outside the team?).

### 6. Provisional themes

- **Insight:** the 2–5 patterns the problems and questions cluster into. Step 2 builds one question block per theme.
- **Format:** one line per theme: **name** — the pattern · items it groups (§3/§5 refs) · evidence strength (strong / some / anecdotal) · recurring? .
- **Depth trap:** themes that are just categories ("Process", "Tech"). Name the pattern: *"stories start before they're ready"*.

### 7. Gaps to fill before the meeting

- Missing numbers, unknown owners/status of carry-over items, people not yet heard from. Each with who can fill it.

---

## Pre-retro survey (when there's no team input yet)

If the raw folder has no team input, step 1 offers this async survey to send out, then stops. Keep it to five questions, anonymous by default:

1. What helped you most this cycle? (one or two things)
2. What slowed you down or frustrated you most? (one or two things)
3. What worries you about the next cycle?
4. Last retro we committed to: {carry-over list}. Which of these made a difference, and which didn't happen?
5. One thing you'd change about how we work — or a question you want answered in the retro.

Optional pulse (1–5): workload sustainability · clarity of priorities · confidence in what we ship.
