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

| Parameter    | Description                                         | Required | Default                                              |
| ------------ | --------------------------------------------------- | -------- | ---------------------------------------------------- |
| `patch_file` | Filename or full path to the `.patch` file          | Yes      | —                                                    |
| `patch_dir`  | Directory to search when `patch_file` is a filename | No       | `$CHANGE_MANAGEMENT_REPO_PATH`, else `.` (cwd)       |

**Patch directory resolution** (precedence, highest first):

1. **`patch_dir` parameter** (ephemeral) — use it if the caller passed one.
2. **`$CHANGE_MANAGEMENT_REPO_PATH`** (durable env var) — else use it if set and non-empty.
3. **Current folder** (`.`) — fallback only when neither above is configured.

If `patch_file` is a plain filename (no `/`), prepend the resolved directory.
If `patch_file` is an absolute or relative path (contains `/`), use it as-is.

## Workflow

### 0. Resolve Patch Path

```bash
PATCH_DIR="${patch_dir:-${CHANGE_MANAGEMENT_REPO_PATH:-.}}"
# If patch_file has no directory component, prepend PATCH_DIR
case "$patch_file" in
  */*) PATCH_PATH="$patch_file" ;;
  *)   PATCH_PATH="$PATCH_DIR/$patch_file" ;;
esac
echo "Resolving patch: $PATCH_PATH"
```

### 1. Validate Patch File

Check the file exists and is readable:

```bash
if [ ! -f "$PATCH_PATH" ]; then
    echo "Error: Patch file not found: $PATCH_PATH"
    exit 1
fi
```

### 2. Check Patch Applicability

Dry-run to verify the patch can be applied cleanly:

```bash
git apply --check "$PATCH_PATH"
```

If this fails, report the conflicts and stop.

### 3. Apply Patch

```bash
git apply "$PATCH_PATH"
```

### 4. Verify Application

Check what changed:

```bash
git status --short
```

### 5. Report Results

Output summary:

```
Patch applied: $PATCH_PATH

Changes applied:
{git status output}

Files modified: {count}
```

Then, without waiting for confirmation, auto-chain into `/change-management-1-stage`
with the files that were actually applied (excluding any skipped/conflicting paths) —
per the router's Auto-Chaining rule. Only pause instead of chaining if `--check` failed
outright and nothing was applied, or if conflicts leave it unclear what should be staged.

To discard the applied changes if needed:
```bash
git checkout -- .
```

## Edge Cases

**Patch file not found:** Report the resolved path (`$PATCH_PATH`) and which directory was used, so the user can verify `CHANGE_MANAGEMENT_REPO_PATH` or `patch_dir`.

**Patch conflicts:** If `--check` fails, report which files conflict:

```bash
git apply --check "$PATCH_PATH" 2>&1
```

Suggest options:
- Fix conflicts manually then retry
- Use `git apply --3way` for three-way merge
- Use `git apply --reject` to apply what can be applied and save rejected hunks

**Already applied:** If the patch was already applied (no changes after apply), report "Patch appears to already be applied or results in no changes."

**Reverse apply:** Mention that user can reverse a patch with:
```bash
git apply --reverse "$PATCH_PATH"
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
