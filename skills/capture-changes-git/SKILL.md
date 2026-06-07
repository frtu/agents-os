---
name: capture-changes-git
description: >
  Stage git changes and create structured change log entry. Captures input sources,
  produced outputs, and context. Use as post-process after ingest or interview skills,
  or when the user says "stage changes", "capture changes", "prepare for commit".
allowed-tools: Bash Read Edit Glob
---

# Capture Changes (Git)

Stage all files created or modified during a workflow and create a structured change log entry.

## When to Use

Call this skill at the end of any workflow that:
- Reads input sources (from `raw/`)
- Produces wiki pages (new or updated)
- Should be tracked as a logical unit of work

Common callers:
- `/second-brain-ingest`
- `/interview-1-preparation`
- `/interview-2-post-review`

## Input Parameters

When invoking this skill, provide:

| Parameter       | Description                                         | Example                                                                                  |
| --------------- | --------------------------------------------------- | ---------------------------------------------------------------------------------------- |
| `trigger`       | Original user instruction that started the workflow | `ingest article on Competency Framework`                                                 |
| `operation`     | Type of operation performed                         | `ingest`, `pre-interview`, `post-interview`                                              |
| `subject`       | Short name for the change set                       | `access-control-systems`, `Candidate Fred T`                                             |
| `input_files`   | List of source files read                           | `raw/notes/Competency Framework.md`, `raw/People/Candidates/Candidate Fred T/Resume.pdf` |
| `created_files` | List of new wiki pages created                      | `wiki/sources/source-competency-framework.md`, `wiki/concepts/patterns/rbac.md`          |
| `updated_files` | List of existing pages updated                      | `wiki/portal.md`, `wiki/log.md`                                                          |

## Workflow

### 1. Stage All Changes

Stage every file created or modified during the workflow:

```bash
git add \
    {input_files...} \
    {created_files...} \
    {updated_files...}
```

**Rules:**
- Stage by explicit path — never use `git add .` or `git add -A`
- Include input sources from `raw/` (important for tracking what was processed)
- Include all wiki pages (new and updated)
- Include `wiki/portal.md` and `wiki/log.md` if touched

### 2. Verify Staged Files

Run `git status` to confirm only intended files are staged:

```bash
git status --short
```

Review output:
- `A` = new file (should match `created_files`)
- `M` = modified file (should match `updated_files` + input files)
- `??` = untracked (should NOT be staged unless intentional)

If unexpected files are staged, unstage them:
```bash
git reset HEAD {unexpected-file}
```

### 3. Create Change Log Entry

Append a structured context block to the most recent log entry in `wiki/log.md`.

**Format:**

```markdown
**Change context:**
```
{operation}: {subject}
Trigger: {original user instruction}
Input: {input_files as comma-separated list}
Created: {created_files as comma-separated list}
Updated: {updated_files as comma-separated list}
```
```

**Example for ingest:**

```markdown
**Change context:**
```
ingest: access-control-systems
Trigger: ingest article on access control
Input: raw/notes/access-control-article.md
Created: source-access-control.md, rbac.md, abac.md, iam.md, policy.md
Updated: portal.md, log.md
```
```

**Example for interview:**

```markdown
**Change context:**
```
pre-interview: Fred T
Trigger: prepare for interview with Fred T
Input: raw/People/Candidates/Fred T/Resume.pdf, raw/People/Candidates/Fred T/Briefing.md
Created: source-fred-t.md
Updated: portal.md, log.md
```
```

### 4. Report Results

Output a summary:

```
Staged {N} files:
- Input sources: {count}
- New pages: {count}
- Updated pages: {count}

Change context appended to wiki/log.md.

Ready to commit. Run: git commit
```

## Do NOT Commit

This skill stages changes but does NOT commit them. The user decides when to commit.

To commit later:
```bash
git commit
```

The change context block in `wiki/log.md` can be used as the commit message body.

## Integration with Calling Skills

### From `/second-brain-ingest`

At step 10, instead of inline git operations, call:

```
/capture-changes-git
  trigger: {user's original instruction}
  operation: ingest
  subject: {source-name}
  input_files: {raw files processed}
  created_files: {wiki pages created}
  updated_files: {wiki pages updated + portal.md + log.md}
```

### From `/interview-1-preparation`

At the end of the workflow:

```
/capture-changes-git
  trigger: {user's original instruction}
  operation: pre-interview
  subject: {Candidate Name}
  input_files: {raw files in candidate folder}
  created_files: {source page created}
  updated_files: {log.md}
```

### From `/interview-2-post-review`

At the end of the workflow:

```
/capture-changes-git
  trigger: {user's original instruction}
  operation: post-interview
  subject: {Candidate Name}
  input_files: {transcript and other raw files}
  created_files: {evaluation page created}
  updated_files: {source page, log.md}
```

## Edge Cases

**No changes to stage:** If no files were created or modified, skip staging and report "No changes to capture."

**Partial staging:** If some files fail to stage (permission issues, etc.), report which files failed and continue with the rest.

**Missing log.md:** If `wiki/log.md` doesn't exist, warn the user but still stage files. The change context can be added manually later.

**Multiple log entries:** Always append to the MOST RECENT log entry (the one at the top of the file, after the frontmatter).
