# Case A — Contribution sources plus a resume → wiki → director-lens resume review

**Ask (paraphrased):** ingest into the vault (engineering-manager vision, competencies, team members,
features built, with outcomes). Review the resume with the director-review skill, using the profile export and
the yearly contribution notes as annexes. Workflow: atomic pages first → bubble up into coarser references →
an external doc on how to improve the resume, without modifying the original. Fan out sub-agents.

**Vault:** a people/management vault (`<vault>`). The full page list is in the vault's `wiki/log.md`
entry for this run.

**Sources (4):** resume PDF, profile-export PDF, team rollup + EM contribution (md, ~160 lines), per-member
team syntheses (md, ~250 lines).

## Lane plan as run

| Phase | Lane            | Scope                                                     | Template    |
| ----- | --------------- | --------------------------------------------------------- | ----------- |
| 1     | members         | `people/members/` (x engineers)                           | atomic      |
| 1     | features-specs  | `product/features/`, `product/specs/`                     | atomic      |
| 1     | patterns        | `concepts/patterns/`, `people/competencies/`              | atomic      |
| 1     | sources-profile | `sources/`, subject profile files (exact)                 | atomic      |
| 2     | product-rollup  | `product/entities/`, 2 synthesis files, features (append) | bubble-up   |
| 2     | evidence-map    | 1 synthesis file, profile (append Related)                | bubble-up   |
| 3     | deliverable     | `output/resume-review-*.md`                               | deliverable |

The deliverable lens was the director-review skill in adversarial mode, run non-interactively, followed by
the word-level clarity skill.

## What made the parallel writers safe

- Feature slugs were fixed in the plan and handed to the members and patterns lanes before anyone wrote. All
  forward links resolved once phase 1 ended.
- The portal, the log and the subject's profile page each had exactly one owner.
- Phase 2 read wiki pages only, so every number in a synthesis cites an atomic page.

## Gate findings that needed action

- **ABSPATH:** a worker wrote `[[<Workspace>/<vault>/xx/yy/culture|Culture]]`.
  Fixed to `[[culture|Culture]]`. This is now automated by `check_links.py --fix-abspath`.
- **Pre-existing broken links:** `[[Full Name]]`-style links in the profile page predated the run.
  Fixed to `[[full-name|Full Name]]` once the member pages existed.
- **Mixed edits:** several pattern and competency pages had the user's own uncommitted edits before the run.
  Staging included both. This is now detected as `PRE_DIRTY` from the baseline.
- **Earlier staged work:** another ingest was already staged, so it landed in the same commit.
  It was named in the commit message.

## Lessons

1. **Read the deliverable's evidence early.** The resume's own defects (unfilled placeholders, inconsistent
   counts, stale metrics) showed up on a first read. Surfacing them to the user early set
   expectations for phase 3.
2. **Profile exports disagree with resumes.** Dates and titles conflicted. Have the sources-profile lane return
   an explicit contradiction list (manifest `gaps`), so the deliverable can turn it into "Unresolved" questions.
3. **Attribution.** Team outcomes in a personal resume must read "led the team that…". Put that rule in the
   deliverable brief, not only in the lens skill.
4. **Two sources, two numbers.** When the sources disagree (time to production: 6 vs 7 weeks), keep both values
   on the feature page under a Caveat. Never average them.
5. **Separate the evidence map from the review.** A phase-2 evidence-map page (framework → evidence → present in the
   artifact? → strength, plus hero facts and an inconsistency ledger) let the phase-3 worker write the review from
   one reference instead of re-reading 30 pages.
