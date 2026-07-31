---
name: lint-unformat
description: Clean up Slack formatting with emoji images, Zoom speaker images, and whitespace issues. Use when the user says "clean slack", "normalize slack emoji", "unformat slack", "clean zoom transcript", or has markdown files with Slack emoji image syntax like `![:emoji:](url)` or Zoom speaker images like `![Speaker 1](https://...zoom.com/...)`.
version: 0.3.0
---

# Lint Emoji Unformat

Clean up Slack-style emoji, Zoom speaker images, and whitespace issues in markdown files.

## What It Does

### Image Normalization

Transforms image markdown to plain text:

| Before                                          | After       |
| ----------------------------------------------- | ----------- |
| `![:tada:](https://emoji.slack-edge.com/...)`   | `:tada:`    |
| `[![:done:](https://emoji.slack-edge.com/...)]` | `[:done:]`  |
| `![Speaker 1](https://us01cnst1.zoom.com/...)`  | `Speaker 1` |
| `![alt](data:image/png;base64,...)`             | `alt`       |

### Whitespace Cleanup

Fixes common Slack export whitespace issues:

| Issue                              | Fix                                          |
| ---------------------------------- | -------------------------------------------- |
| Trailing spaces on blank lines     | Removed                                      |
| Trailing double-space on content   | **Preserved** (Slack line break syntax)      |
| Multiple consecutive blank lines   | Collapsed to single blank line               |
| Missing newline at end of file     | Added                                        |

## Usage

Run the Python script on markdown files. **Always use `--normalize-whitespace`** to also clean up blank lines and trailing spaces.

```bash
# Single file
python3 .claude/commands/lint-unformat/scripts/normalize_image_links.py --normalize-whitespace /path/to/file.md

# Dry run (preview changes)
python3 .claude/commands/lint-unformat/scripts/normalize_image_links.py --dry-run --normalize-whitespace /path/to/file.md

# Process multiple files
python3 .claude/commands/lint-unformat/scripts/normalize_image_links.py --normalize-whitespace file1.md file2.md

# Process all files in a directory
python3 .claude/commands/lint-unformat/scripts/normalize_image_links.py --normalize-whitespace /path/to/_reports_/*.md
```

## Script

Located at `scripts/normalize_image_links.py` within this command folder.

## When to Use

- After copying content from Slack that contains custom emoji
- When ingesting Slack exports or transcripts into the wiki
- When markdown files have broken emoji image links from Slack
- After exporting Zoom transcripts that contain speaker avatar images
- When files have trailing whitespace or excessive blank lines from copy-paste
