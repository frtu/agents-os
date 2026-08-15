---
name: lint-unformat
description: Clean up Slack formatting with emoji images, Zoom speaker images, whitespace issues, code block formatting, unescaped table wikilinks, and misaligned markdown tables. Use when the user says "clean slack", "normalize slack emoji", "unformat slack", "clean zoom transcript", "normalize code blocks", "clean whitespace", "remove blank lines", "fix table wikilinks", "escape wikilinks", "align tables", "format tables", "line up pipes", or has markdown files with Slack emoji image syntax, Zoom speaker images, code blocks with extra blank lines, wikilinks with unescaped pipes in tables, or ragged/misaligned table columns.
version: 0.5.0
---

# Lint Unformat

Clean up Slack-style emoji, Zoom speaker images, whitespace issues, and code block formatting in markdown files. Normalizers can be run independently or all together.

## Normalizers

| Name                | Flag                | What it does                                                        |
| ------------------- | ------------------- | ------------------------------------------------------------------- |
| **images**          | `--images`          | Converts Slack emoji and Zoom speaker images to plain text          |
| **whitespace**      | `--whitespace`      | Collapses blank lines, trims trailing spaces, ensures final newline |
| **code-blocks**     | `--code-blocks`     | Removes blank lines inside fenced code blocks                       |
| **table-wikilinks** | standalone script   | Escapes unescaped pipes in wikilinks inside table rows              |
| **align-tables**    | standalone script   | Pads table columns so pipes align vertically to the widest cell     |

## Procedure

1. **Parse the ARGUMENTS** to determine which normalizer(s) to run:
   - If user says "images", "emoji", "slack emoji", "zoom" → use `--images`
   - If user says "whitespace", "blank lines", "trailing spaces" → use `--whitespace`
   - If user says "code blocks", "code block cleanup" → use `--code-blocks`
   - If user says "table wikilinks", "escape wikilinks", "fix table links" → run the standalone `fix-table-wikilinks.py` script (see below)
   - If user says "align tables", "format tables", "normalize tables", "line up pipes" → run the standalone `align-tables.py` script (see below)
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

## Standalone: table-wikilinks

Escapes unescaped pipes in wikilinks that appear inside table rows so Obsidian
renders them correctly: `[[link|name]]` → `[[link\|name]]`. Only touches lines
starting with `|` and skips `raw/` directories (immutable sources).

This runs as a separate script (not part of `normalize_markdown.py`):

```bash
# Fix a single file or directory
python3 .claude/commands/lint-unformat/scripts/fix-table-wikilinks.py /path/to/file.md
python3 .claude/commands/lint-unformat/scripts/fix-table-wikilinks.py /path/to/dir
# Dry run (preview changes)
python3 .claude/commands/lint-unformat/scripts/fix-table-wikilinks.py --dry-run .
# Verbose (show before/after per line)
python3 .claude/commands/lint-unformat/scripts/fix-table-wikilinks.py --verbose .
```

## Standalone: align-tables

Reformats every GitHub-style markdown table so the pipes line up vertically:
each column is padded to the width of its widest cell. Per-column alignment
declared in the separator row is preserved (`:---` left, `---:` right, `:---:`
centered, `---` default). Cell width is measured visually (CJK/fullwidth
characters count as 2), and escaped pipes (`\|`) inside wikilinks are treated as
literal text so cells are not split. A table must have a separator row as its
second line to be reformatted; `raw/` directories are skipped.

This runs as a separate script (not part of `normalize_markdown.py`):

```bash
# Align tables in a single file or directory
python3 .claude/commands/lint-unformat/scripts/align-tables.py /path/to/file.md
python3 .claude/commands/lint-unformat/scripts/align-tables.py /path/to/dir
# Dry run (preview which tables would change)
python3 .claude/commands/lint-unformat/scripts/align-tables.py --dry-run .
# Verbose (show line range of each reformatted table)
python3 .claude/commands/lint-unformat/scripts/align-tables.py --verbose .
```

> Tip: run `fix-table-wikilinks.py` before `align-tables.py` so escaped pipes
> are correct before column widths are computed.
