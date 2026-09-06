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

## Workflow Patterns

### Pattern 0: Resume from git (optional opener)

At the start of a session, before any change:

1. Run `/change-management-0-resume` (reads the latest commit by default; pass a
   count to read more) to reconstruct what was previously done
2. Continue into Pattern A, B, or C as needed

### Pattern A: Stage + Log (most common)

After ingest or interview workflows:

1. Run `/change-management-1-stage` with file lists
2. Run `/change-management-9-log` to create commit message and log entry

### Pattern B: Refactor + Stage + Log

When reorganizing wiki structure:

1. Run `/change-management-2-refactor` to move files
2. Run `/change-management-1-stage` to stage all changes
3. Run `/change-management-9-log` to create commit message and log entry

### Pattern C: Diff + Apply (stash alternative)

When preserving changes across branch switches or sessions:

1. Run `/change-management-7-diff` to export current changes to a `.patch` file
2. Switch branches, reset, or start new session
3. Run `/change-management-8-apply {patch-file}` to restore the changes

### Pattern D: Single Phase

Run any phase standalone when only that step is needed.

## Integration with Other Skills

These skills call change-management phases at their end:

- `/second-brain-ingest` → calls `-1-stage` then `-9-log`
- `/interview-1-preparation` → calls `-1-stage` then `-9-log`
- `/interview-3-post-review` → calls `-1-stage` then `-9-log`
- `/second-brain-area` → calls `-2-refactor` then `-1-stage` then `-9-log`
