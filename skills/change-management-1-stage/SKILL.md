---
name: change-management-1-stage
description: >
  Stage git changes via git add. Use as post-process after ingest or interview
  skills, or when the user says "stage changes", "git add", "prepare for commit".
allowed-tools: Bash Read Edit Glob
---

# Change Management: Stage (git add)

Stage all files created or modified during a workflow.

## When to Use

Call this skill at the end of any workflow that:
- Reads input sources (from `raw/`)
- Produces wiki pages (new or updated)
- Should be tracked as a logical unit of work

Common callers:
- `/second-brain-ingest`
- `/interview-1-preparation`
- `/interview-3-post-review`

## Input Parameters

| Parameter       | Description                                         | Example                                                                                  |
| --------------- | --------------------------------------------------- | ---------------------------------------------------------------------------------------- |
| `input_files`   | List of source files read                           | `raw/notes/Competency Framework.md`, `raw/People/Candidates/Candidate Fred T/Resume.pdf` |
| `created_files` | List of new wiki pages created                      | `wiki/sources/source-competency-framework.md`, `wiki/concepts/patterns/rbac.md`          |
| `updated_files` | List of existing pages updated                      | `wiki/portal.md`                                                                         |

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
- Include `wiki/portal.md` if touched

**Gotcha — a path silently refuses to stage.** If `git add {path}` prints `The following paths are ignored by one of your .gitignore files` (or the file just never appears in `git status`), a **global** gitignore is catching it. A bare pattern like `area_name` in `~/.gitignore_global` matches any `product/area_name/` directory. 

Force-stage the intended files explicitly:

```bash
git check-ignore -v xx/wiki/product/area_name   # shows which ignore rule + file matched
git add -f xx/wiki/product/area_name/           # -f overrides the ignore for these paths only
```

Print all the force-added wiki pages you deliberately created.

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

### 3. Report Results

Output a summary:

```
Staged {N} files:
- Input sources: {count}
- New pages: {count}
- Updated pages: {count}

Ready for /change-management-9-log to create commit message.
```

## Do NOT Commit

This skill stages changes but does NOT commit them. Run `/change-management-9-log`
next to create the commit message and log entry.

## Integration with Calling Skills

### From `/second-brain-ingest`

At step 10, call:

```
/change-management-1-stage
  input_files: {raw files processed}
  created_files: {wiki pages created}
  updated_files: {wiki pages updated + portal.md}
```

Then call `/change-management-9-log` with operation details.

### From `/interview-1-preparation`

At the end of the workflow:

```
/change-management-1-stage
  input_files: {raw files in candidate folder}
  created_files: {source page created}
  updated_files: {}
```

Then call `/change-management-9-log` with operation details.

### From `/interview-3-post-review`

At the end of the workflow:

```
/change-management-1-stage
  input_files: {transcript and other raw files}
  created_files: {evaluation page created}
  updated_files: {source page}
```

Then call `/change-management-9-log` with operation details.

## Edge Cases

**No changes to stage:** If no files were created or modified, skip staging and report "No changes to capture."

**Partial staging:** If some files fail to stage (permission issues, etc.), report which files failed and continue with the rest.
