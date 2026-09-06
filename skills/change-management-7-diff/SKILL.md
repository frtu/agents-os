---
name: change-management-7-diff
description: >
  Create a diff patch file from current changes. Uses --staged if staged changes
  exist, otherwise exports unstaged changes. Use when the user says "create patch",
  "export diff", "save changes to patch", or wants to preserve local changes.
allowed-tools: Bash Read
---

# Change Management: Diff (export patch)

Export current git changes to a local `.patch` file for later application.

## When to Use

Call this skill when:
- User wants to save local changes before switching branches
- User wants to share a diff without committing
- User wants a backup of in-progress work
- User says "create patch", "export diff", "save patch"

## Input Parameters

| Parameter     | Description                                      | Required | Default   |
| ------------- | ------------------------------------------------ | -------- | --------- |
| `output_path` | Directory path where patch file will be written  | No       | `.` (cwd) |

## Workflow

### 1. Determine Diff Mode

Check if staged changes exist:

```bash
git diff --cached --quiet
```

- Exit code 0 = no staged changes → use unstaged diff
- Exit code 1 = staged changes exist → use `--staged`

### 2. Generate Timestamp

Create filename with datetime:

```bash
date +%Y%m%d-%H%M%S
```

Format: `YYYYMMDD-HHMMSS.patch` (e.g., `20260904-143052.patch`)

### 3. Export Diff

**If staged changes exist:**
```bash
git diff --staged > {output_path}/{timestamp}.patch
```

**If no staged changes (use unstaged):**
```bash
git diff > {output_path}/{timestamp}.patch
```

### 4. Validate Patch

Check that the patch file is non-empty:

```bash
if [ -s {output_path}/{timestamp}.patch ]; then
    echo "Patch created successfully"
else
    echo "Warning: No changes to export"
    rm {output_path}/{timestamp}.patch
fi
```

### 5. Report Results

Output summary:

```
Patch exported: {output_path}/{timestamp}.patch
Mode: {staged | unstaged}
Size: {file size}

To apply later:
  /change-management-8-apply {output_path}/{timestamp}.patch
  
To apply manually:
  git apply {output_path}/{timestamp}.patch
```

## Edge Cases

**No changes:** If both staged and unstaged diffs are empty, report "No changes to export" and skip creating the patch file.

**Output path doesn't exist:** Create the directory if it doesn't exist.

**Mixed staged/unstaged:** Only exports one type (staged takes precedence). If user has both and wants all changes, they should stage everything first or run the skill twice with different modes.

## Integration

This skill pairs with `/change-management-8-apply`:

```
/change-management-7-diff
    ↓ (creates patch file)
... time passes, branch switches, etc ...
    ↓
/change-management-8-apply {patch-file}
    ↓ (restores changes)
```
