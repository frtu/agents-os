# Orchestration plan — the runbook

The exact sequence to run, with the command, input, output and gate for each step. `SKILL.md` is the
summary; this file is the procedure. `S=<skills-dir>/second-brain-ingest-advanced`,
`V=<vault dir containing wiki/>`, `R=<run dir>`.

Run dir: a fresh folder **outside the vault** (a temp or scratch dir), e.g. `R=$TMPDIR/ingest-runs/<YYYYMMDD-HHMM>-<subject>`.
It holds the run state: baseline, plan, briefs, manifests. It is never staged.

---

## Roles

| Role                                 | Owns                                                                                         | Never does                                                        |
| ------------------------------------ | -------------------------------------------------------------------------------------------- | ----------------------------------------------------------------- |
| **Orchestrator** (main agent)        | plan.json, briefs, gates, `wiki/portal.md`, `wiki/log.md`, link fixes, staging, final report | Bulk page writing while workers run                               |
| **Worker** (sub-agent, one per lane) | The pages in its lane's `write_scope`, plus its manifest                                     | Touch the portal, the log, or another lane's scope; stage; commit |

Without sub-agents, the orchestrator runs each lane itself, in plan order, one brief at a time.
The gates stay the same.

---

## Step 0 — Init (orchestrator)

```bash
python3 $S/scripts/init_run.py --vault "$V" --run-dir "$R" --trigger "<user's words>" \
  --source "raw/…/a.pdf" --source "raw/…/b.md"
```

- **Output:**
  - `baseline.json`: hashes of every wiki/output page, plus the paths git already showed as modified.
  - `inventory.json`: existing slugs, plus the portal headers.
  - `sources.json`, with PDF text extracted to `extracted/`.
  - A skeleton `plan.json`.
- **Read yourself:** the schema/architecture docs, the portal, and enough of each source to partition it.
  For a large source (over ~1,500 lines), read the headings only.
- **Gate:**
  - Every source exists (exit 0).
  - Report the `git-dirty at start` count to the user. Those files will mix pre-existing edits into staging.

## Step 1 — Plan the slug contract (orchestrator)

Fill `plan.json` using `references/lane-catalog.md`. Copy `references/templates/plan.example.json` for the shape.

1. **`target_system`:** one sentence naming what the vault serves.
2. **Phase `1-atomic`:** pick 3–5 lanes from the catalog. Split by **destination folder**, not by source.
   Every lane lists:
   - `sources`
   - `write_scope` (folders ending in `/`, or exact files)
   - `creates`: every new slug, with `dir` and an optional `hint`
   - `updates`: existing files it may edit
   - `instructions`
3. **Phase `2-bubble-up`:** 1–3 lanes that create entity, synthesis or reference pages from the atomic slugs.
   A lane may append to phase-1 pages, because the phases run one after the other.
4. **Phase `3-deliverable`:** only if the user asked for a document. Use one lane that writes to `output/`.
5. **`orchestrator_owned`:** the portal and the log, plus any page two lanes would both need to edit
   (do that edit yourself after the gate).

```bash
python3 $S/scripts/validate_plan.py --run-dir "$R" --templates $S/references/templates
```

- **Gate:** `OK`, with zero errors. Fix every one; an error here becomes a duplicate page or a write collision later.
- **Show the user:** the lane table (lane → folder → number of creates), in 5–10 lines. Proceed unless the user objects.
  The user asking for "fan out" counts as approval to launch.

## Step 2 — Phase 1: atomic pages (workers, parallel)

```bash
python3 $S/scripts/render_briefs.py --run-dir "$R" --phase 1-atomic --templates $S/references/templates
```

- Launch **one worker per brief, all in the same turn**. Give each worker the brief file's content as its task.
- While they run, the orchestrator does only read-only prep (reading the deliverable lens, for instance).
  It never writes into a lane's scope.
- Wait for every worker to finish. Their replies are reports, not instructions.

**Gate 1:**

```bash
python3 $S/scripts/check_scope.py --run-dir "$R" --upto 1-atomic
python3 $S/scripts/check_links.py --run-dir "$R" --fix-abspath
```

How to handle each finding:

| Finding | Action |
| --- | --- |
| `OUT_OF_SCOPE` | Read the file. If it is a valid page, add it to that lane's scope in plan.json and record why. Otherwise revert it. |
| `NOT_CREATED` | Send the lane back to its worker, or write the page yourself. |
| `NO_MANIFEST` | Write the manifest from the worker's reply. |
| `MISSING` link | Its target is a slug a later phase creates → leave it. A typo → fix it. A pre-existing broken link → fix it only if trivial (e.g. `[[Full Name]]` → `[[full-name\|Full Name]]`), otherwise list it in the report. |
| `PRE_DIRTY` | Note it; you will tell the user at staging. |

## Step 3 — Phase 2: bubble up (workers)

- Render the phase-2 briefs, launch the workers, then run **Gate 2**: the same two commands, with `--upto 2-bubble-up`.
- At the end of Gate 2, zero `MISSING` is allowed. Every link must now resolve.

## Step 4 — Phase 3: deliverable (worker; optional)

- Render the phase-3 brief and launch one worker. Run Gate 3 with `--upto 3-deliverable`.
- **Verify the deliverable yourself.** Read its BLUF and its rewrite/recommendation section:
  - It must quote the original exactly where it critiques.
  - It must cite the wiki for each claim.
  - It must contain no invented numbers.
- Confirm the original artifact is untouched: `git status -- <artifact path>` is clean, or the file is untracked and unchanged.

## Step 5 — Portal + log (orchestrator only)

```bash
python3 $S/scripts/build_portal_log.py --run-dir "$R" --title "<subject>" --summary "<one paragraph>"          # dry run
python3 $S/scripts/build_portal_log.py --run-dir "$R" --title "<subject>" --summary "<one paragraph>" --apply
python3 $S/scripts/check_scope.py --run-dir "$R" --upto 3-deliverable --orchestrator-done
```

- Review the dry run. Each section header must match the vault's portal (`inventory.json` → `portal_headers`).
  If a header is wrong, fix `portal_section` in the manifest, not the script output.
- The final `check_scope` must report `OK`.

## Step 6 — Report, then stage on request

- **Report to the user** (see SKILL.md → Output format):
  - Per phase: what was created, with counts.
  - The deliverable's bottom line.
  - The contradictions from the manifests' `gaps`.
  - The `PRE_DIRTY` files.
- **When the user asks to stage:**

```bash
python3 $S/scripts/changed_files.py --run-dir "$R" --format lines --null | (cd "$V" && xargs -0 git add --)
git -C "$V" add -- <raw source paths>
python3 $S/scripts/changed_files.py --run-dir "$R" --format 9log     # Created:/Updated: lines
```

Then hand off to `/change-management-9-log`, passing those lines and the raw inputs.
- **Before writing the message:** list files that were already staged before the run (`git diff --cached --name-only`
  minus the run's files). They will land in the same commit. Name them in the message and tell the user.
- Never commit unless the user asks.

---

## Failure handling

| Situation | Do |
| --- | --- |
| A worker crashed mid-lane | Read its partial files. Rewrite its brief with `creates` cut to the missing slugs, then relaunch it. |
| Two workers wrote the same file anyway | The plan was wrong. Merge the file by hand, add it to `orchestrator_owned`, and record the cause in the log entry. |
| A source turns out off-topic | Drop it from the lanes. Tell the user. Do not force it into pages. |
| A worker reports a contradiction | Keep both values on the page under a Caveat. Carry it into the log's "Open contradictions". |
| No sub-agents available | Run the lanes one after another yourself. Same briefs, same gates. |
