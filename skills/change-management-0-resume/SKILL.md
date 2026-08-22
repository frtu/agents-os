---
name: change-management-0-resume
description: >
  Optional first step in change workflows. Reads recent git history to reconstruct
  what was previously done, summarizes it for the user, and asks clarifying
  questions only if needed. Use when the user says "resume", "what was I doing",
  "pick up where we left off", or wants context before starting new changes.
allowed-tools: Bash Read AskUserQuestion
---

# Change Management: Resume (context from git)

Optional first step in any change workflow. Reconstructs recent context by reading
the local git project's latest commit(s) so subsequent work builds on what was
already done.

## When to Use

Call this skill when:
- Starting a new session and needing to recall the last unit of work
- The user says "resume", "what did we do last", "pick up where we left off"
- A change workflow should be grounded in prior context before staging/refactoring

This phase is **optional** — skip it when the current task is self-contained.

## Input Parameters

| Parameter | Description                                        | Default | Example |
| --------- | -------------------------------------------------- | ------- | ------- |
| `count`   | Number of recent commits to read for context       | `1`     | `5`     |

Only load more than 1 commit when the user explicitly asks (e.g. "resume from the
last 5 commits", "read the last 3 commits").

## Workflow

### 1. Read Recent Git History

Read the latest `{count}` commit(s) — subject, body, and changed files:

```bash
git log -n {count} --stat --pretty=format:'%h%x09%an%x09%ad%x09%s%n%b' --date=short
```

If the change-management log convention is in use, the commit body already carries
the structured **Change context** block (operation, trigger, input, created,
updated). Extract those fields directly.

For a lighter view of just what files moved:

```bash
git log -n {count} --name-status --pretty=format:'%h %s' --date=short
```

Also check for uncommitted work that may be mid-flight:

```bash
git status --short
```

### 2. Reconstruct Context

From the commit(s), determine:
- **What** was done (the operation: ingest, refactor, interview, etc.)
- **Why** (the trigger / original instruction, if captured in the body)
- **Which files** were created, updated, or moved
- **Whether** there is uncommitted work still open (`git status`)

### 3. Summarize for the User

Provide a concise summary of what you learned:

```
Resumed context from {count} commit(s):

Last change: {type}: {subject}
  Operation: {operation}
  Trigger:   {trigger}
  Files:     {N created, M updated, K moved}

Uncommitted: {summary of git status, or "clean working tree"}
```

Keep it tight — one block, no filler.

### 4. Ask Clarifications — Only If Needed

Ask clarifying questions **only when the reconstructed context is ambiguous** and
would change how you proceed. Examples of when to ask:
- Uncommitted changes exist and it is unclear whether to continue or discard them
- The last commit's intent is unclear and the next step depends on it
- Multiple plausible continuations exist

If the context is clear, **do not ask** — just report the summary and proceed.
Use `AskUserQuestion` for any clarification.

## Edge Cases

**No commits:** If the repo has no history, report "No git history to resume from"
and proceed without context.

**Shallow / detached state:** If `git log` fails, report the error and continue
without blocking the workflow.

**count exceeds history:** If fewer commits exist than requested, read all
available and note how many were found.

## Integration

This skill is the optional opening step in change workflows:

```
/change-management-0-resume  ← you are here (optional)
    ↓
/change-management-1-stage   (or -2-refactor)
    ↓
/change-management-9-log
    ↓
user: git commit
```
