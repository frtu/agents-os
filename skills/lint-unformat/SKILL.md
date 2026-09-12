---
name: lint-unformat
description: Clean up Slack formatting with emoji images, Zoom speaker images, whitespace issues, code block formatting, unescaped table wikilinks, misaligned markdown tables, and missing wikilinks. Use when the user says "clean slack", "normalize slack emoji", "unformat slack", "clean zoom transcript", "normalize code blocks", "clean whitespace", "remove blank lines", "fix table wikilinks", "escape wikilinks", "align tables", "format tables", "line up pipes", "relink wiki", "add wikilinks", "auto-link mentions", "unformat", "lint", or has markdown files with Slack emoji image syntax, Zoom speaker images, code blocks with extra blank lines, wikilinks with unescaped pipes in tables, ragged/misaligned table columns, or unlinked mentions of pages that exist.
version: 0.7.0
---

# Lint Unformat

Clean up Slack-style emoji, Zoom speaker images, whitespace issues, and code block formatting in markdown files.

## Default Behavior (Run All)

**When invoked without specific flags, run ALL normalizers.** This is the expected behavior for "unformat", "lint", "clean up", etc.

```bash
# DEFAULT: Run all normalizers (images + whitespace + code-blocks)
python3 {skill_base}/scripts/normalize_markdown.py /path/to/file.md
```

This single command applies:
- **images**: Slack emoji URLs → `:emoji:`, Zoom speaker images → plain text
- **whitespace**: Collapse blank lines, trim trailing spaces, ensure final newline
- **code-blocks**: Remove blank lines inside fenced code blocks

**IMPORTANT:** Do NOT use the old `normalize_image_links.py` script — it only handles images. Always use `normalize_markdown.py` which runs all normalizers by default.

## Normalizers

| Name                | Flag                | What it does                                                        |
| ------------------- | ------------------- | ------------------------------------------------------------------- |
| **images**          | `--images`          | Converts Slack emoji and Zoom speaker images to plain text          |
| **whitespace**      | `--whitespace`      | Collapses blank lines, trims trailing spaces, ensures final newline |
| **code-blocks**     | `--code-blocks`     | Removes blank lines inside fenced code blocks                       |
| **table-wikilinks** | standalone script   | Escapes unescaped pipes in wikilinks inside table rows              |
| **align-tables**    | standalone script   | Pads table columns so pipes align vertically to the widest cell     |
| **relink-wiki**     | standalone script   | Adds wikilinks for unlinked mentions of pages that exist in the wiki |

## Procedure

1. **Determine target files** from ARGUMENTS:
   - If ARGUMENTS specifies file paths → use those
   - If ARGUMENTS says "local files" or "modified files" → get from `git status --porcelain | grep -E '^\s*M.*\.md$' | sed 's/^...//'`
   - If ARGUMENTS says "all files" → use `find . -name "*.md" -type f`

2. **Parse which normalizer(s) to run** (default = ALL):
   - **Default / "unformat" / "lint" / "clean" / "all"** → run with NO flags (applies images + whitespace + code-blocks)
   - "images", "emoji", "slack emoji", "zoom" → use `--images` only
   - "whitespace", "blank lines", "trailing spaces" → use `--whitespace` only
   - "code blocks", "code block cleanup" → use `--code-blocks` only
   - "table wikilinks", "escape wikilinks", "fix table links" → run standalone `fix-table-wikilinks.py`
   - "align tables", "format tables", "line up pipes" → run standalone `align-tables.py`
   - "relink wiki", "add wikilinks", "auto-link mentions" → run standalone `relink-wiki.py`

3. **Run the normalizer** (always use `normalize_markdown.py`, never `normalize_image_links.py`):
   ```bash
   # Default: all normalizers
   python3 {skill_base}/scripts/normalize_markdown.py [FILES...]
   
   # With specific flags (only if user explicitly requested a subset)
   python3 {skill_base}/scripts/normalize_markdown.py --images [FILES...]
   ```

4. **Report summary** from script output.

> **Deprecated:** `normalize_image_links.py` and `normalize_whitespaces.py` are legacy scripts. Always use `normalize_markdown.py` which consolidates all normalizers.

## Examples

```bash
# ═══════════════════════════════════════════════════════════════════
# DEFAULT: All normalizers (images + whitespace + code-blocks)
# This is what "unformat", "lint", "clean" should run
# ═══════════════════════════════════════════════════════════════════
python3 {skill_base}/scripts/normalize_markdown.py /path/to/file.md
python3 {skill_base}/scripts/normalize_markdown.py file1.md file2.md

# Dry run (preview changes without modifying)
python3 {skill_base}/scripts/normalize_markdown.py --dry-run /path/to/file.md

# ═══════════════════════════════════════════════════════════════════
# Single normalizer (only if user explicitly requests a subset)
# ═══════════════════════════════════════════════════════════════════
python3 {skill_base}/scripts/normalize_markdown.py --images /path/to/file.md
python3 {skill_base}/scripts/normalize_markdown.py --whitespace /path/to/file.md
python3 {skill_base}/scripts/normalize_markdown.py --code-blocks /path/to/file.md

# Multiple specific normalizers
python3 {skill_base}/scripts/normalize_markdown.py --whitespace --code-blocks /path/to/file.md
```

> `{skill_base}` = the skill's base directory (e.g., `/Users/fred.tu/git/ai/agents-os-frtu/skills/lint-unformat`)

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

## Standalone: relink-wiki

Adds wikilinks for plain-text mentions of pages that already exist in the wiki
but aren't linked yet. It builds a vocabulary from the wiki's content folders
(`concepts`, `product`, `resources`, `people`, `projects`, `synthesis`),
generates display-name variations per page slug (Title Case, CamelCase, plus a
small acronym alias table like CDC → Change Data Capture), then links the **first**
unlinked occurrence of each term per file: `[[slug|Display]]`. Existing
wikilinks, code blocks, inline code, frontmatter, and URLs are protected and
never touched. `README.md`/`log.md`/`portal.md`/`index.md` and the `sources/`
folder are skipped.

This runs as a separate script. The path argument is the wiki root, relative or 
absolute (default `wiki`). Run it from a vault directory so `wiki` resolves to that vault's wiki:

```bash
# Relink a vault wiki (run from the vault directory, e.g. search/)
python3 ../.claude/commands/lint-unformat/scripts/relink-wiki.py wiki
# Dry run (preview links that would be added)
python3 ../.claude/commands/lint-unformat/scripts/relink-wiki.py wiki --dry-run --verbose
# Only one page (relative to the wiki root, or absolute)
python3 ../.claude/commands/lint-unformat/scripts/relink-wiki.py wiki --file concepts/patterns/strong-authorisation.md
```

> Tip: run this after ingest, then follow with `fix-table-wikilinks.py` so any
> new links that landed inside tables get their pipes escaped.
