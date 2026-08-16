---
name: change-management-2-refactor
description: >
  Refactor file paths using git mv. Use when the user says "move files", "rename",
  "refactor structure", "reorganize", or needs to relocate wiki pages while
  preserving git history.
allowed-tools: Bash Read Edit Glob
---

# Change Management: Refactor (git mv)

Move or rename files using `git mv` to preserve git history and update references.

## When to Use

Call this skill when:
- Reorganizing wiki structure (moving pages between folders)
- Renaming files or directories
- Consolidating scattered pages into a new area
- Splitting a folder into subcategories

## Input Parameters

| Parameter     | Description                              | Example                                    |
| ------------- | ---------------------------------------- | ------------------------------------------ |
| `moves`       | List of source → destination mappings    | `wiki/old/page.md → wiki/new/page.md`      |
| `reason`      | Why the refactor is needed               | `Consolidating access-control pages`       |

## Workflow

### 1. Validate Moves

For each move, verify:
- Source path exists
- Destination parent directory exists (create if needed)
- No file exists at destination (would overwrite)

```bash
# Check source exists
ls -la {source}

# Check destination parent exists
ls -d $(dirname {destination})

# Check destination doesn't exist
! ls {destination} 2>/dev/null
```

### 2. Execute Moves

Use `git mv` to preserve history:

```bash
git mv {source} {destination}
```

For directory moves:
```bash
git mv {source_dir}/ {destination_dir}/
```

**Rules:**
- Always use `git mv`, never `mv` + `git add`
- Create parent directories first if needed: `mkdir -p $(dirname {destination})`
- Move one path at a time for clear error messages

### 3. Update References

After moving files, update wikilinks in:
- `wiki/portal.md` — update any links to moved pages
- Other wiki pages that reference moved files
- `wiki/log.md` — if it references moved pages

Search for broken references:
```bash
# Find files referencing the old path
grep -r "old-filename" wiki/ --include="*.md"
```

Update each reference:
```bash
# In the referencing file, replace old path with new
```

### 4. Verify State

Run `git status` to confirm moves are staged:

```bash
git status --short
```

Expected output shows renames:
- `R  old/path.md -> new/path.md`

### 5. Report Results

```
Refactored {N} files:
- {source1} → {destination1}
- {source2} → {destination2}

Updated {M} references in:
- portal.md
- other-page.md

All moves staged. Ready for /change-management-9-log.
```

## Do NOT Commit

This skill moves files but does NOT commit. Run `/change-management-9-log` next to
create the commit message and log entry.

## Edge Cases

**Destination exists:** Abort that move, report the conflict, continue with others.

**Source doesn't exist:** Skip that move, report it, continue with others.

**Circular moves:** Detect A→B, B→A patterns and abort with warning.

**Directory with contents:** `git mv` handles this correctly, but verify all contents
moved by checking `git status`.
