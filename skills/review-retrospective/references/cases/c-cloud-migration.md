---
case: C
team: Platform Engineering — cloud migration (illustrative)
format: Sailboat — Island (goal) / Wind (helps) / Anchors (slows) / Rocks (risks), dot-voted
pattern: Metaphor board mapped to the template; forward-looking risks with no home; generic stickies that could fit any team
sub-areas: [Migration squad, Developer platform, SRE]
retros: [2026-07-30]
source: "synthetic — generified from public Sailboat retrospective examples; not a real team"
---

# Case C — Platform Engineering, cloud migration (illustrative)

> Synthetic example of a **Sailboat** retro mid-way through a multi-quarter migration off an on-prem data centre. Shows the mapping from metaphor columns to the template, and what to do with **Rocks** (risks), which the standard sections don't hold.

## Team context

- **Sub-areas:** Migration squad (moving services), Developer platform (CI/CD, templates), SRE (on-call, reliability).
- **Group "Needs improvement" by:** Priorities & capacity · Tooling & tech debt · People & sustainability.
- **Recurring themes:** migration pace vs BAU load; dependency on a third-party managed service; key-person risk.
- **Key metrics to ask for:** services migrated / total, migration burn-up vs plan, on-call pages / week, overtime or after-hours deploys, open tech-debt items blocking migration.

## Format mapping used

| Sailboat column | Template section | Note |
|---|---|---|
| **Island** (goal) | Summary — the direction; metadata goal | The yardstick for everything else |
| **Wind** (helps) | What went well | Ask for evidence per sticky |
| **Anchors** (slows) | Needs improvement | Symptom → impact → cause |
| **Rocks** (risks ahead) | **Risks to watch** (added sub-section after Needs improvement) | Not a pain yet: needs a trigger/early signal and an owner, not necessarily an action |
| Dot votes | Priority of themes / actions | Top-voted anchor/rock must reach the action table or be explicitly parked |

---

## Retro 2026-07-30

### Raw input (as captured, votes in brackets)

**Island**
- Complete migration to the new cloud platform by end of year
- Strong, positive team culture
- Hit all project deadlines this fiscal year

**Wind**
- Strong team spirit and collaboration (2)
- Supportive leadership, clear vision for the migration
- Dedicated learning time for the new platform
- Access to modern tooling (IaC, managed services)
- Regular feedback from internal customers (service teams)

**Anchors**
- Lack of clear priorities — migration vs BAU tickets (6)
- Technical debt in legacy services slows each move (5)
- Too few people for the scope; overallocation (4)
- Inconsistent communication with service teams about cut-over dates (3)
- Outdated deploy tooling on the legacy side
- Resistance to change from some service teams

**Rocks**
- Burnout from sustained high workload (5)
- Dependency on a third-party managed database service (3)
- Key person leaving — only one person knows the legacy network setup (4)
- Unforeseen technical challenges in the last services
- Changing regulatory requirements on data residency (2)

No owners, no dates, no metrics. "Migration 40% done" mentioned verbally.

### Review findings

1. **The Island has three goals, one of which is real** — "migrate by end of year" is the goal; "strong culture" and "all deadlines" are aspirations that can't steer trade-offs. Keep one Island, with a number (services migrated / total).
2. **Top-voted anchor is a decision, not a task** — "migration vs BAU priorities" (6) can't be fixed by the team; it needs a leadership call. Action = *escalate with a proposal* (e.g. BAU capped at N% of capacity), owner = manager, date.
3. **Rocks need a home** — risks aren't pains yet. Add a *Risks to watch* list: risk → early signal → owner → mitigation. Only the top one or two become actions.
4. **Burnout (5) and overallocation (4) are the same theme** — and the sharpest one. It must appear in the summary, not buried. Ask for an observable: after-hours deploys, pages/week, leave not taken.
5. **Key-person risk (4) is cheap to act on now** — a pairing/documentation action this cycle; expensive once it fires.
6. **Generic stickies** — "strong team spirit", "access to modern tooling", "unforeseen challenges" could come from any team. Ask *which* moment or tool, or fold them in without weight.
7. **Wind has no evidence** — "supportive leadership" and "learning time" are likely real; one concrete example each (e.g. "leadership deferred feature X to free two engineers").
8. **Contradiction** — "clear vision" (wind) vs "lack of clear priorities" (anchor, 6 votes): vision on *where*, no clarity on *what first*. Say so; it sharpens the escalation.
9. **Headline number is verbal** — "40% done" must be written, sourced, and compared to plan (ahead/behind?).

### Produced report — key sections

**Summary**

> The migration is **`[need input]` 40% complete** (`[need input]`: vs plan) and the team is carrying it on goodwill: collaboration and leadership backing are strong, but **priorities between migration and BAU are unresolved**, and the load is showing — **burnout was the top-voted risk**. Direction: get an explicit capacity split and remove single points of failure before the final, hardest services.
>
> - **Biggest wins** — team collaboration; leadership backing; learning time for the new platform.
> - **Top pain points** — migration vs BAU priority conflict; legacy tech debt slowing each move; overallocation.
> - **Where the team wants to go** — a sustainable pace to year-end with no single points of failure.

**Risks to watch**

| Risk | Votes | Early signal | Owner | Mitigation |
|---|---|---|---|---|
| Burnout from sustained load | 5 | after-hours deploys / pages trending up; leave not taken | `[need input]` (manager) | Action #1 capacity split; review monthly |
| Key person (legacy network) leaves | 4 | — (binary) | `[need input]` | Action #2 pairing + runbook |
| Managed DB service dependency | 3 | vendor incidents, support SLA misses | `[need input]` | Exit/fallback note by Q4 |
| Data-residency regulation change | 2 | legal/compliance notice | `[need input]` | Check-in with compliance each quarter |

**Action items**

| # | Action item | Theme | Owner | Priority | Due | Success signal |
|---|---|---|---|---|---|---|
| 1 | Propose migration/BAU capacity split to leadership and get a decision | Priorities | `[need input]` (manager) | High | 2026-08-13 | Written split agreed; BAU ≤ agreed % next sprint |
| 2 | Pair a second engineer on legacy network; write cut-over runbook | Key-person risk | `[need input]` | High | 2026-08-27 | Second person runs one cut-over solo |
| 3 | List tech-debt items blocking remaining services; fix-or-bypass decision per item | Tech debt | `[need input]` | High | 2026-08-20 | List exists; each item has a decision |
| 4 | Publish cut-over calendar to service teams, one channel | Communication | `[need input]` | Med | 2026-08-06 | No "surprise" cut-overs raised at next retro |

"Resistance to change" and "outdated legacy tooling" are parked: both shrink as migration proceeds.

### Carry-over for next retro

Check: capacity decision (#1) and whether burnout signals moved · second engineer on legacy network (#2) · tech-debt decisions (#3) · cut-over calendar (#4) · migration % vs plan.
