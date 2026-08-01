---
name: lint-unformat
description: Clean up Slack formatting with emoji images, Zoom speaker images, whitespace issues, and code block formatting. Use when the user says "clean slack", "normalize slack emoji", "unformat slack", "clean zoom transcript", "normalize code blocks", "clean whitespace", "remove blank lines", or has markdown files with Slack emoji image syntax, Zoom speaker images, or code blocks with extra blank lines.
version: 0.4.0
---

# Lint Unformat

Clean up Slack-style emoji, Zoom speaker images, whitespace issues, and code block formatting in markdown files. Normalizers can be run independently or all together.

## Normalizers

| Name            | Flag            | What it does                                                        |
| --------------- | --------------- | ------------------------------------------------------------------- |
| **images**      | `--images`      | Converts Slack emoji and Zoom speaker images to plain text          |
| **whitespace**  | `--whitespace`  | Collapses blank lines, trims trailing spaces, ensures final newline |
| **code-blocks** | `--code-blocks` | Removes blank lines inside fenced code blocks                       |

## Procedure

1. **Parse the ARGUMENTS** to determine which normalizer(s) to run:
   - If user says "images", "emoji", "slack emoji", "zoom" → use `--images`
   - If user says "whitespace", "blank lines", "trailing spaces" → use `--whitespace`
   - If user says "code blocks", "code block cleanup" → use `--code-blocks`
   - If user says "all" or doesn't specify → run with no flags (applies all three)

2. **Determine target files**:
   - If ARGUMENTS specifies file paths → use those
   - If ARGUMENTS says "local files" or "modified files" → get from `git status --porcelain | grep -E '^\s*M.*\.md$' | sed 's/^...//'`
   - If ARGUMENTS says "all files" → use `find . -name "*.md" -type f`

3. **Run the normalizer**:
   ```bash
   python3 .claude/commands/lint-unformat/scripts/normalize_markdown.py [FLAGS] [FILES...]
   ```

4. **Report summary** from script output.

## Examples

```bash
# All normalizers (default)
python3 .claude/commands/lint-unformat/scripts/normalize_markdown.py /path/to/file.md
# Single normalizer
python3 .claude/commands/lint-unformat/scripts/normalize_markdown.py --images /path/to/file.md
python3 .claude/commands/lint-unformat/scripts/normalize_markdown.py --whitespace /path/to/file.md
python3 .claude/commands/lint-unformat/scripts/normalize_markdown.py --code-blocks /path/to/file.md
# Multiple normalizers
python3 .claude/commands/lint-unformat/scripts/normalize_markdown.py --whitespace --code-blocks /path/to/file.md
# Dry run
python3 .claude/commands/lint-unformat/scripts/normalize_markdown.py --dry-run /path/to/file.md
# Multiple files
python3 .claude/commands/lint-unformat/scripts/normalize_markdown.py file1.md file2.md
```

## Normalizer Details

### images
Transforms image markdown to plain text:
- `![:tada:](https://emoji.slack-edge.com/...)` → `:tada:`
- `![Speaker 1](https://us01cnst1.zoom.com/...)` → `Speaker 1`
- `![alt](data:image/png;base64,...)` → `alt`

### whitespace
- Removes trailing spaces on blank lines
- Preserves trailing double-space on content (Slack line break syntax)
- Collapses multiple consecutive blank lines to one
- Ensures file ends with newline

### code-blocks
Removes blank lines inside fenced code blocks (between triple backticks).
