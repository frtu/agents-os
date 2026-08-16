---
name: change-management-9-log
description: >
  Final step in change workflows. Creates a structured commit message, displays it
  for user to copy, then appends to wiki/log.md. Use after staging or refactoring
  when ready to document the change.
allowed-tools: Bash Read Edit Glob
---

# Change Management: Log

Final step in any change workflow. Creates a structured commit message and logs it.

## When to Use

Call this skill after:
- `/change-management-1-stage` has staged files
- `/change-management-2-refactor` has moved files
- Any workflow that should be documented before commit

## Input Parameters

| Parameter       | Description                                         | Example                                          |
| --------------- | --------------------------------------------------- | ------------------------------------------------ |
| `operation`     | Type of operation performed                         | `ingest`, `refactor`, `pre-interview`            |
| `subject`       | Short name for the change set                       | `access-control-systems`, `Candidate Fred T`     |
| `trigger`       | Original user instruction                           | `ingest article on access control`               |
| `input_files`   | List of source files read                           | `raw/notes/article.md`                           |
| `created_files` | List of new pages created                           | `wiki/sources/source-article.md`                 |
| `updated_files` | List of pages updated                               | `wiki/portal.md`                                 |
| `moved_files`   | List of moves (for refactor operations)             | `old/path.md → new/path.md`                      |

## Workflow

### 1. Generate Commit Message

Create a structured commit message following conventional format:

**Format:**
```
{type}: {subject}

{operation}: {subject}
Trigger: {original user instruction}
Input: {input_files as comma-separated list}
Created: {created_files as comma-separated list}
Updated: {updated_files as comma-separated list}
Moved: {moved_files if any}
```

**Type mapping:**
- `ingest` → `feat`
- `refactor` → `refactor`
- `pre-interview`, `post-interview` → `feat`
- `fix` → `fix`

**Example:**
```
feat: ingest access-control-systems

ingest: access-control-systems
Trigger: ingest article on access control
Input: raw/notes/access-control-article.md
Created: source-access-control.md, rbac.md, abac.md
Updated: portal.md, log.md
```

### 2. Display for User

Output the commit message in a copyable format:

```
╔══════════════════════════════════════════════════════════════════╗
║ COMMIT MESSAGE — copy below                                       ║
╠══════════════════════════════════════════════════════════════════╣

feat: ingest access-control-systems

ingest: access-control-systems
Trigger: ingest article on access control
Input: raw/notes/access-control-article.md
Created: source-access-control.md, rbac.md, abac.md
Updated: portal.md, log.md

╚══════════════════════════════════════════════════════════════════╝
```

### 3. Append to wiki/log.md

Find the most recent log entry (first entry after frontmatter) and append
the change context block.

**Log entry format:**
```markdown
**Change context:**
```
{operation}: {subject}
Trigger: {trigger}
Input: {input_files}
Created: {created_files}
Updated: {updated_files}
```
```

**Location:** Append to the MOST RECENT entry in `wiki/log.md` (the first
`## YYYY-MM-DD` section after frontmatter).

### 4. Stage log.md

```bash
git add wiki/log.md
```

### 5. Report Completion

```
Change logged.

Files staged: {N}
Log entry appended to wiki/log.md

To commit:
  git commit -m "$(pbpaste)"   # if you copied the message
  git commit                   # to edit interactively
```

## Edge Cases

**Missing log.md:** Warn user but still display commit message. They can create
log.md manually or commit without the log entry.

**No recent entry:** If log.md has no `## YYYY-MM-DD` entries, create a new one
for today's date.

**Empty operation:** If no files were changed, report "No changes to log" and skip.

## Integration

This skill is the final step in change workflows:

```
/second-brain-ingest
    ↓
/change-management-1-stage
    ↓
/change-management-9-log  ← you are here
    ↓
user: git commit
```
