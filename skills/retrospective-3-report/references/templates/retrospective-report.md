# Retrospective Report — template & authoring guide

A reusable structure for a **team retrospective report**: the doc that turns a retro session (board, sticky notes, meeting notes) into a short, decision-ready record of what worked, what hurt, and what the team commits to change. Team-agnostic — a team's own history lives in the vault's retrospective folder (prep files and past reports); `../cases/` holds synthetic worked examples.

Use it in **Produce mode** to author a report from raw retro input, or as a checklist in **Review mode** to see what a draft is missing.

---

## How to use this file

Each section below has three parts:

- **Insight it must deliver** — the one thing the reader should *know or decide* after reading it. If a section doesn't move the reader, cut it.
- **Style & format** — how it should read and look on the page.
- **Questions to answer** — fire these at the raw input (or the facilitator). A section is done when every question has a concrete answer — a **number, a name, or a date**, not an adjective.

**Golden rule (the whole doc in one line):** a retro is judged by the **action items that actually change next cycle** — owned, dated, few — not by how many sticky notes it captured. Everything else is evidence for those actions.

---

## The structural spine

1. Metadata
2. Summary (BLUF)
3. Previous action items — follow-up
4. What went well
5. Needs improvement
   5b. Risks to watch (optional — when the board has a risks column)
6. Start / Stop / Continue
7. Action items
8. Carry-over for next retro
9. Appendix — prep file & raw input

A reader with one minute reads 2 and 7 and knows what the team learned and what changes. Sections 4–6 are the evidence; 3 and 8 are the accountability loop (8 is what the next retro's prep checks).

---

## 1. Metadata

- **Insight it must deliver:** which team, which cycle, who was in the room.
- **Style & format:** compact header block.

  ```markdown
  **Team:** {team / sub-teams}
  **Cycle:** {sprint / period covered, e.g. YYYY-MM-DD → YYYY-MM-DD}
  **Date held:** {YYYY-MM-DD}
  **Facilitator:** {name}
  **Participants:** {names or headcount}
  **Previous retro:** {link}
  **Prep file:** {link to the pre-meeting dossier, if any}
  **Format:** {board format, e.g. Sailboat, 4Ls, WRAP} · **Goal (if the retro was called for one):** {question to answer}
  ```
- **Questions to answer:**
  - What period does this retro cover (start and end date)?
  - Who facilitated, and who will own follow-up of the action items?
  - Where is the previous retro, so the action-item loop can be closed?
  - Was the retro called to answer a specific question (evaluate a pilot, close a project)? Then the summary must answer it.

## 2. Summary (BLUF)

- **Insight it must deliver:** the cycle's **headline** in one sentence, the trade-off it exposes, and the direction the team chose. A reader who stops here knows the story.
- **Style & format:** one opening paragraph (2–3 sentences, headline first, key number in bold), then exactly three bullets:
  - **Biggest wins** — the 3–5 that matter, strongest first.
  - **Top pain points** — the 3–5 that cost the most (toil, incidents, cost, morale).
  - **Where the team wants to go** — the direction, as a theme, not a list.
- **Questions to answer:**
  - If this cycle had one headline, what is it — and what's the number behind it?
  - What is the flip side of the headline (the cost, the load, the risk it created)?
  - Which *theme* ties the pain points together (e.g. manual toil, missing ownership, unclear priorities)?
  - Is every number in the summary consistent with the body, and scoped correctly (prod vs non-prod, one service vs all)?
  - If the retro had a stated goal or decision to make, does the first paragraph answer it (or say who decides by when)?
- **Depth trap:** a summary that re-lists the sections. The summary names the **pattern**; the sections hold the items.

## 3. Previous action items — follow-up

- **Insight it must deliver:** did last retro's commitments happen? A retro that never checks its own actions teaches the team that retros don't matter.
- **Style & format:** a short table carried from the previous retro (the prep file's carry-over section, with statuses confirmed in the meeting).

  | # | Action item (from {previous date}) | Owner | Status | Outcome / note |
  |---|---|---|---|---|
  | 1 | … | … | Done / In progress / Dropped / Not started | one line: what changed, or why dropped |
- **Questions to answer:**
  - Which previous actions are done, and did they fix the pain they targeted?
  - Which slipped — and is the reason capacity, ownership, or the action was wrong?
  - Which pain points reappear this cycle? (A recurring pain with a "done" action means the action missed the root cause.)
  - Was anything dropped that this retro raises again? Then the drop was wrong — restore it.
  - Did any previous action vanish without a status? Force a decision: carry, drop, or done.
- **Depth trap:** silently re-adding last cycle's undone items as new ones. Carry them over explicitly or drop them explicitly.

## 4. What went well

- **Insight it must deliver:** what to protect and repeat — with enough evidence that the team (and a manager reading it) believes it.
- **Style & format:** bullets, strongest first, one win per bullet. Each bullet = **outcome + evidence** (a number, a dashboard link, a before/after). Group by sub-area only if the team has distinct workstreams.
- **Questions to answer:**
  - What is the measurable outcome of each win, and where is the evidence (metric, dashboard, incident count)?
  - Is the scope of each claim honest (non-prod vs prod, one service vs the fleet, one week vs trend)?
  - Which win was caused by a deliberate team choice (so it should be repeated) vs luck/external?
- **Depth trap:** vibes without evidence ("X works well") and duplicates phrased differently. Merge, quantify, or cut.

## 5. Needs improvement

- **Insight it must deliver:** the problems that cost the team the most, **with their root cause** where known — not a complaint list.
- **Style & format:** grouped by sub-area / workstream (use the team's own split — see its case file). Each bullet: **symptom → impact → cause** (e.g. "Jobs crash after hours → on-call paged, rarely actionable → snapshot step runs out of memory"). Bold the one or two that hurt most.
- **Questions to answer:**
  - What is the impact of each problem — on-call pages, hours of toil, cost, user-facing incidents, morale?
  - Is the root cause known, suspected, or unknown? Say which.
  - Does any item contradict a "What went well" item (e.g. "more stable" vs "stability issues")? Reconcile the scope.
  - Which problems are recurring from previous retros?
- **Depth trap:** symptoms without cause lead to actions like "improve X". If the cause is unknown, the action is "investigate X by {date}", not "fix X".

## 5b. Risks to watch (optional)

- **Insight it must deliver:** what could hurt next cycle that isn't hurting yet — so it's watched, not forgotten.
- **Style & format:** a short table, highest-voted first.

  | Risk | Votes | Early signal | Owner | Mitigation |
  |---|---|---|---|---|
- **Questions to answer:**
  - Is this already hurting? If yes, it belongs in §5, not here.
  - What observable signal would tell us it's materialising?
  - Which one or two are cheap to act on now (key-person risk, single vendor)? Those become actions.
- **Depth trap:** turning every risk into an action. Most risks need an owner and a signal, not work.

## 6. Start / Stop / Continue

- **Insight it must deliver:** the team's behavioural and process changes — the *how we work* layer, not a second backlog.
- **Style & format:** three short lists, one line each, verb-first.
  - **Start** — new practices or capabilities to introduce.
  - **Stop** — practices that waste time or hurt; be concrete ("stop X at Y").
  - **Continue** — practices that worked and are at risk of being dropped.
- **Questions to answer:**
  - Is each item a behaviour or practice the team controls — or a project that belongs in the backlog?
  - Does every Start/Stop that matters have a matching action item (Section 7)?
  - Is anything in "Continue" actually new work in disguise ("continue building X")? If so, it's a roadmap item, not a retro action.
- **Depth trap:** copying every Start/Stop/Continue line into the action table verbatim. The table should be the *filtered, owned* subset.

## 7. Action items

- **Insight it must deliver:** the few commitments the team will actually execute next cycle, each with an owner, a date, and a way to know it worked.
- **Style & format:** one table, ordered by priority.

  | # | Action item | Theme | Owner | Priority | Due | Success signal |
  |---|---|---|---|---|---|---|
  | 1 | verb-first, specific, scoped | from §5/§6 | one name | High / Med / Low | date or sprint | metric or observable change |

  Rules:
  - **Owner is a name**, never `TBD` or "team". An unowned action is a wish.
  - **Cap High priority at ~3.** If everything is high, nothing is.
  - **Every High item traces to a top pain point** in the summary.
  - **Success signal is observable** ("after-hours pages < N/week", "zero data loss at peak") — not "improved".
  - **Split investigate vs fix** when the root cause is unknown.
  - Roadmap/continuing investments go in a separate "Ongoing investments" line or the team's roadmap, not here.
- **Questions to answer:**
  - Who owns each item by name, and have they agreed?
  - Which three items, if done, would remove the most pain next cycle?
  - Did the top-voted items reach this table — or are they explicitly parked with a reason?
  - Does any action just restate the problem ("try to…", "find better ways to…")? Rewrite as verb + scope + owner.
  - How will we know at the next retro that each item worked?
  - Is anything here too big for one cycle? Break it down or name the first step.
- **Depth trap:** a dozen-row table with every owner `TBD` and half the rows High. That is a backlog dump, not a commitment.

## 8. Carry-over for next retro

- **Insight it must deliver:** exactly what the next retro must check — so the loop closes without anyone re-reading this report.
- **Style & format:** one short list: each action (with its success signal), each risk's early signal, each open decision with who decides by when, and any recurring pain to watch.
- **Questions to answer:**
  - For each High action, what number or observable will we look at next time?
  - Which pain, if it shows up again, should become the next headline?

## 9. Appendix — prep file & raw input

- **Insight it must deliver:** traceability — the prep dossier, the original board/notes/interviews, so nothing the team said is lost in curation.
- **Style & format:** links to the prep file and raw files; facilitation-guide questions **not reached** in the meeting; collapse raw sticky notes under a heading if useful. No editing of the raw text.

---

## Style rules for the whole document

1. **Headline first.** The summary opens with the cycle's one story and its number.
2. **Themes over lists.** Group items into 2–4 themes; name the pattern, not just the items.
3. **Evidence or scope it down.** Every win and pain carries a number, a link, or an honest qualifier (non-prod, anecdotal).
4. **Symptom → impact → cause.** Problems without a cause produce vague actions.
5. **Few, owned, dated actions.** Named owner, due date, success signal. Cap High priority.
6. **Close the loop.** Always review the previous retro's actions before writing new ones.
7. **Blameless.** Describe systems and processes, not people.
8. **Consistent numbers.** The same metric must read the same everywhere in the doc.
9. **Format-independent.** Whatever the board format, map it to this spine (`retro-formats.md`); votes set priority.

## The one-minute self-review (fire before you send)

- Can a reader get the cycle's story from the first paragraph?
- Were last retro's action items reviewed?
- Is there a carry-over list the next retro can check without re-reading the report?
- Does every High action trace to a top pain point, with a named owner and a date?
- Are there ≤ 3 High priority items?
- Is every win backed by evidence and correctly scoped?
- Does any number or claim contradict another section?
- Is any "action item" really an ongoing roadmap investment?
- If the retro was called for a decision, is it answered?
- Did every top-voted item reach an action or get parked explicitly?
