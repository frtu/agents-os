---
name: change-management-8-apply
description: >
  Apply a patch file to the local repository. Use when the user says "apply patch",
  "restore from patch", or provides a .patch file to apply.
allowed-tools: Bash Read
---

# Change Management: Apply (apply patch)

Apply a previously exported `.patch` file to the current working tree.

## When to Use

Call this skill when:
- User wants to restore changes from a saved patch
- User says "apply patch", "restore patch", "git apply"
- User provides a `.patch` file path

## Input Parameters

| Parameter    | Description                    | Required |
| ------------ | ------------------------------ | -------- |
| `patch_file` | Path to the `.patch` file      | Yes      |

## Workflow

### 1. Validate Patch File

Check the file exists and is readable:

```bash
if [ ! -f "{patch_file}" ]; then
    echo "Error: Patch file not found: {patch_file}"
    exit 1
fi
```

### 2. Check Patch Applicability

Dry-run to verify the patch can be applied cleanly:

```bash
git apply --check "{patch_file}"
```

If this fails, report the conflicts and stop.

### 3. Apply Patch

```bash
git apply "{patch_file}"
```

### 4. Verify Application

Check what changed:

```bash
git status --short
```

### 5. Report Results

Output summary:

```
Patch applied: {patch_file}

Changes applied:
{git status output}

Files modified: {count}

To stage these changes:
  /change-management-1-stage
  
To discard if needed:
  git checkout -- .
```

## Edge Cases

**Patch file not found:** Report error with the exact path and suggest checking the path.

**Patch conflicts:** If `--check` fails, report which files conflict:

```bash
git apply --check "{patch_file}" 2>&1
```

Suggest options:
- Fix conflicts manually then retry
- Use `git apply --3way` for three-way merge
- Use `git apply --reject` to apply what can be applied and save rejected hunks

**Already applied:** If the patch was already applied (no changes after apply), report "Patch appears to already be applied or results in no changes."

**Reverse apply:** Mention that user can reverse a patch with:
```bash
git apply --reverse "{patch_file}"
```

## Integration

This skill pairs with `/change-management-7-diff`:

```
/change-management-7-diff
    ↓ (creates patch file)
... time passes, branch switches, etc ...
    ↓
/change-management-8-apply {patch-file}  ← you are here
    ↓ (restores changes)
/change-management-1-stage
    ↓
/change-management-9-log
```
