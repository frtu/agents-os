#!/usr/bin/env python3
"""
Convert Slack emoji image syntax to plain text emoji syntax in markdown files.

Example:
    ![:tada-animated:](https://emoji.slack-edge.com/T086B9BTPEJ/tada-animated/3743b73b31c22c82.gif)
    -> :tada-animated:

    [![:done:](https://emoji.slack-edge.com/T086B9BTPEJ/done/c11bf3db1f90897f.jpg)]
    -> [:done:]
"""

import re
import sys
from pathlib import Path


def normalize_slack_emoji(content: str) -> str:
    """
    Replace Slack emoji image syntax with plain text emoji syntax.

    Patterns handled:
    1. ![:emoji_name:](url) -> :emoji_name:
    2. [![:emoji_name:](url)] -> [:emoji_name:]
    """
    # Pattern 1: ![:emoji_name:](url) -> :emoji_name:
    pattern1 = r'!\[(:[\w-]+:)\]\([^)]+\)'
    content = re.sub(pattern1, r'\1', content)

    # Pattern 2: [![:emoji_name:](url)] -> [:emoji_name:]
    pattern2 = r'\[!\[(:[\w-]+:)\]\([^)]+\)\]'
    content = re.sub(pattern2, r'[\1]', content)

    return content


def process_file(filepath: Path, dry_run: bool = False) -> tuple[bool, int]:
    """
    Process a single markdown file.

    Returns:
        (changed, num_replacements)
    """
    try:
        original_content = filepath.read_text(encoding='utf-8')
        normalized_content = normalize_slack_emoji(original_content)

        if original_content == normalized_content:
            return False, 0

        num_replacements = len(re.findall(r'!\[(:[\w-]+:)\]|!\[!\[(:[\w-]+:)\]', original_content))

        if not dry_run:
            filepath.write_text(normalized_content, encoding='utf-8')
            print(f"✓ Updated {filepath} ({num_replacements} emoji normalized)")
        else:
            print(f"[DRY RUN] Would update {filepath} ({num_replacements} emoji)")

        return True, num_replacements

    except Exception as e:
        print(f"✗ Error processing {filepath}: {e}", file=sys.stderr)
        return False, 0


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='Normalize Slack emoji syntax in markdown files',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process a single file
  %(prog)s /path/to/file.md

  # Process multiple files
  %(prog)s file1.md file2.md file3.md

  # Process all weekly files in a directory
  %(prog)s /path/to/_weekly_/*.md

  # Dry run (show what would be changed without modifying files)
  %(prog)s --dry-run /path/to/file.md
        """
    )

    parser.add_argument(
        'files',
        nargs='+',
        type=Path,
        help='Markdown file(s) to process'
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be changed without modifying files'
    )

    args = parser.parse_args()

    total_files = 0
    total_changed = 0
    total_replacements = 0

    for filepath in args.files:
        if not filepath.exists():
            print(f"✗ File not found: {filepath}", file=sys.stderr)
            continue

        if not filepath.is_file():
            print(f"✗ Not a file: {filepath}", file=sys.stderr)
            continue

        total_files += 1
        changed, num_replacements = process_file(filepath, args.dry_run)

        if changed:
            total_changed += 1
            total_replacements += num_replacements

    print(f"\n{'[DRY RUN] ' if args.dry_run else ''}Summary: {total_changed}/{total_files} files modified, {total_replacements} emoji normalized")

    return 0 if total_files > 0 else 1


if __name__ == '__main__':
    sys.exit(main())
