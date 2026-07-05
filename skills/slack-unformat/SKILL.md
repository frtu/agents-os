---
name: slack-unformat
description: Clean up Slack formatting with emoji images and transform to plain markdown. Use when the user says "clean slack", "normalize slack emoji", "unformat slack", or has markdown files with Slack emoji image syntax like `![:emoji:](url)`.
version: 0.1.0
---

# Slack Unformat

Clean up Slack-style emoji image syntax in markdown files and convert to plain text emoji syntax.

## What It Does

Transforms Slack emoji image markdown to plain text:

| Before                                          | After      |
| ----------------------------------------------- | ---------- |
| `![:tada:](https://emoji.slack-edge.com/...)`   | `:tada:`   |
| `[![:done:](https://emoji.slack-edge.com/...)]` | `[:done:]` |

## Usage

Run the Python script on markdown files:

```bash
# Single file
python3 .claude/commands/slack-unformat/scripts/normalize_slack_emoji.py /path/to/file.md

# Dry run (preview changes)
python3 .claude/commands/slack-unformat/scripts/normalize_slack_emoji.py --dry-run /path/to/file.md

# Process multiple files
python3 .claude/commands/slack-unformat/scripts/normalize_slack_emoji.py file1.md file2.md

# Process all files in a directory
python3 .claude/commands/slack-unformat/scripts/normalize_slack_emoji.py /path/to/_reports_/*.md
```

## Script

Located at `scripts/normalize_slack_emoji.py` within this command folder.

## When to Use

- After copying content from Slack that contains custom emoji
- When ingesting Slack exports or transcripts into the wiki
- When markdown files have broken emoji image links from Slack
