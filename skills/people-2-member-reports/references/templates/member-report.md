# Member Report Page — template

Default skeleton for a direct report's page, used when the vault has no direct-report
pages to copy. Link formats follow `people-ingest/references/people-schema.md`.

**Filename:** `wiki/people/members/{slug}.md`

```markdown
---
Category: people/members
Aliases:
  - {First name}
Tags:
  - member
  - direct-report
  - {track}-track
Source links:
  - [[source-…]]
Created: YYYY-MM-DD
Last Updated: YYYY-MM-DD
---

# {Full Name}

**Role:** [[role-{track}-{level}|{Level} — {Title}]] · **Team:** {team} · **Manager:** {manager}

## Current Profile

{2–4 sentences: scope, what they own, where they are on the ladder.}

## Competency Snapshot

| Competency | Expected ({Level}) | Observed | Evidence |
|------------|--------------------|----------|----------|
| [[{skill}#IC Track Depth Progression\|{Skill}]] | **{depth from role page}** | **{depth}** | [[source-…]] — {one line} |

## Strengths

- {Skill-linked strength} — {evidence}

## Growth Areas

| Competency | Gap / red flag | Growth action | Source of action |
|------------|----------------|---------------|------------------|
| [[{skill}\|{Skill}]] | {observed vs expected} | {action} | [[{skill}#Growth Actions]] |

## Path to {Next Level}

Next: [[role-{track}-{next}|{Next} — {Title}]]

- {Key transition from the role page} — {status / evidence}

## Process Contribution

- [[step-{name}|{Step}]] — {what they do there}

## Evidence Log

- YYYY-MM-DD — [[source-…]] — {what it showed}

## Related

- [[role-{track}-{level}]] · [[{manager-slug}]] · [[{team-page}]]
```

## Per-section guidance

| Section | Insight it gives | Questions to answer | Omit when |
| --- | --- | --- | --- |
| Current Profile | Where the person stands today | What do they own? Since when at this level? | Never — keep at least scope + level |
| Competency Snapshot | Fit to the ladder, skill by skill | Which skills did the evidence actually show? At what depth? | Row: skill not seen in evidence |
| Strengths | What to lean on | Where are they at or above expected depth? | No evidence |
| Growth Areas | What to coach | Which gaps or red flags recur? Which action from the skill page fits? | No gap evidenced |
| Path to Next Level | Promotion readiness | Which next-level transitions are met, in progress, not started? | Terminal level |
| Process Contribution | Where they create value in the SDLC | Which steps do they lead or contribute to? | No evidence |
| Evidence Log | Audit trail across updates | What did each source show? | Never — append on each update |
