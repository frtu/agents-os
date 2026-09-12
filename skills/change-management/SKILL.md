---
name: change-management
description: >
  Router for multi-step change workflows. Stages files, refactors paths, and logs
  changes. Use when the user says "stage changes", "refactor files", "move files",
  or wants to capture a logical unit of work for commit.
allowed-tools: Bash Read Glob AskUserQuestion Skill
---

# Change Management (Router)

Orchestrates change management workflows by chaining sub-skills:

| Phase        | Skill                          | Purpose                                                |
| ------------ | ------------------------------ | ------------------------------------------------------ |
| 0 — Resume   | `change-management-0-resume`   | Reconstruct context from recent git history (optional) |
| 1 — Stage    | `change-management-1-stage`    | Stage files via `git add`                              |
| 2 — Refactor | `change-management-2-refactor` | Move/rename files via `git mv`                         |
| 7 — Diff     | `change-management-7-diff`     | Export changes to a `.patch` file                      |
| 8 — Apply    | `change-management-8-apply`    | Apply a `.patch` file to restore changes               |
| 9 — Log      | `change-management-9-log`      | Generate commit message and append to log              |

This router selects the appropriate phase(s) based on user intent.

## Quick Reference

| User Says                                                          | Route To                       |
| ------------------------------------------------------------------ | ------------------------------ |
| "resume from git", "what was I doing", "pick up where we left off" | `change-management-0-resume`   |
| "stage changes", "git add", "prepare commit"                       | `change-management-1-stage`    |
| "refactor", "move files", "rename", "git mv"                       | `change-management-2-refactor` |
| "create patch", "export diff", "save patch"                        | `change-management-7-diff`     |
| "apply patch", "restore patch"                                     | `change-management-8-apply`    |
| "log changes", "commit message", "capture log"                     | `change-management-9-log`      |
| "stage and log", "full workflow"                                   | Phase 1 → Phase 9              |

## Auto-Chaining (don't stop to reconfirm mid-pattern)

Once the user has kicked off a phase that belongs to one of the patterns below, run the
rest of that pattern straight through — do **not** pause to ask "want me to run the next
step?" between phases. Invoking any phase in a chain is itself the confirmation for the
rest of the chain:

- **Apply succeeds → auto-chain into Stage.** A clean (or partially-clean, with conflicts
  explicitly reported and excluded) `-8-apply` run continues directly into `-1-stage` with
  the files it applied, without waiting for a yes.
- **Stage completes → auto-chain into Log.** A `-1-stage` run (from any source: apply,
  refactor, ingest, direct request) continues directly into `-9-log` once staging is
  reported, without waiting for a yes.
- **Log stops at the commit boundary.** `-9-log` displays the commit message and staged
  file count, then **stops** — never run `git commit` without the user explicitly asking
  for it in that turn (see repo-level git safety rules). This is the one place in the
  chain that still needs a human decision.

Still pause and ask when something in the chain actually needs a decision, not just
because a phase finished:
- a patch conflict was excluded from apply (report it, then still auto-chain the rest)
- staged files don't match what was expected (unexpected `??`/untracked entries)
- the commit `subject`/`trigger` is genuinely ambiguous and guessing would misrepresent
  the change

## Workflow Patterns

### Pattern 0: Resume from git (optional opener)

At the start of a session, before any change:

1. Run `/change-management-0-resume` (reads the latest commit by default; pass a
   count to read more) to reconstruct what was previously done
2. Continue into Pattern A, B, or C as needed

### Pattern A: Stage + Log (most common)

After ingest or interview workflows:

1. Run `/change-management-1-stage` with file lists
2. Auto-chain into `/change-management-9-log` to create the commit message and log
   entry — no reconfirmation between steps 1 and 2 (see Auto-Chaining above)

### Pattern B: Refactor + Stage + Log

When reorganizing wiki structure:

1. Run `/change-management-2-refactor` to move files
2. Auto-chain into `/change-management-1-stage` to stage all changes
3. Auto-chain into `/change-management-9-log` to create commit message and log entry

### Pattern C: Diff + Apply (stash alternative)

When preserving changes across branch switches or sessions:

1. Run `/change-management-7-diff` to export current changes to a `.patch` file
2. Switch branches, reset, or start new session
3. Run `/change-management-8-apply {patch-file}` to restore the changes
4. Auto-chain into `/change-management-1-stage` (and from there into `-9-log`) once
   apply succeeds — no reconfirmation (see Auto-Chaining above)

### Pattern D: Single Phase

Run any phase standalone when only that step is needed.

## Integration with Other Skills

These skills call change-management phases at their end:

- `/second-brain-ingest` → calls `-1-stage` then `-9-log`
- `/interview-1-preparation` → calls `-1-stage` then `-9-log`
- `/interview-3-post-review` → calls `-1-stage` then `-9-log`
- `/second-brain-area` → calls `-2-refactor` then `-1-stage` then `-9-log`
