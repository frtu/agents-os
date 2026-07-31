#!/usr/bin/env python3
"""
Convert Slack emoji and Zoom speaker image syntax to plain text in markdown files.

Examples:
    Slack emoji:
        ![:tada-animated:](https://emoji.slack-edge.com/T086B9BTPEJ/tada-animated/3743b73b31c22c82.gif)
        -> :tada-animated:

        [![:done:](https://emoji.slack-edge.com/T086B9BTPEJ/done/c11bf3db1f90897f.jpg)]
        -> [:done:]

    Zoom speaker images:
        ![Speaker 1](https://us01cnst1.zoom.com/fe-static/recording-player/img/zr_default.b8180c09.png)
        -> Speaker 1

        ![Speaker 1](data:image/png;base64,iVBORw0KGgo...)
        -> Speaker 1
"""

import re
import sys
from pathlib import Path
from typing import Callable, Optional


def normalize_markdown_images(content: str) -> str:
    """
    Replace Slack emoji and Zoom speaker image syntax with plain text.

    Patterns handled:
    1. ![:emoji_name:](url) -> :emoji_name:
    2. [![:emoji_name:](url)] -> [:emoji_name:]
    3. ![Speaker N](https://...zoom.../...) -> Speaker N
    4. ![alt](data:image/...;base64,...) -> alt
    """
    # Pattern 1: ![:emoji_name:](url) -> :emoji_name:
    pattern1 = r'!\[(:[\w-]+:)\]\([^)]+\)'
    content = re.sub(pattern1, r'\1', content)

    # Pattern 2: [![:emoji_name:](url)] -> [:emoji_name:]
    pattern2 = r'\[!\[(:[\w-]+:)\]\([^)]+\)\]'
    content = re.sub(pattern2, r'[\1]', content)

    # Pattern 3: ![Speaker N](https://...zoom.../...) -> Speaker N
    pattern3 = r'!\[(Speaker \d+)\]\(https?://[^)]*zoom*[^)]*\)'
    content = re.sub(pattern3, r'\1', content)

    # Pattern 4: ![alt](data:image/...;base64,...) -> alt
    pattern4 = r'!\[([^\]]*)\]\(data:image/[^;]+;base64,[^)]+\)'
    content = re.sub(pattern4, r'\1', content)

    return content

def process_file(
    filepath: Path,
    dry_run: bool = False,
    normalize_function: Optional[Callable[[str], str]] = None
) -> tuple[bool, int]:
    """
    Process a single markdown file.

    Args:
        filepath: Path to the markdown file
        dry_run: If True, don't write changes
        normalize_function: Optional function to normalize content

    Returns:
        (changed, num_replacements)
    """
    try:
        original_content = filepath.read_text(encoding='utf-8')
        normalized_content = normalize_markdown_images(original_content)
        if normalize_function:
            normalized_content = normalize_function(normalized_content)

        if original_content == normalized_content:
            return False, 0

        # Count all patterns: Slack emoji + Zoom speakers + base64 images
        slack_matches = len(re.findall(r'!\[(:[\w-]+:)\]|\[!\[(:[\w-]+:)\]', original_content))
        zoom_matches = len(re.findall(r'!\[Speaker \d+\]\(https?://[^)]*zoom*[^)]*\)', original_content))
        base64_matches = len(re.findall(r'!\[[^\]]*\]\(data:image/[^;]+;base64,[^)]+\)', original_content))
        num_replacements = slack_matches + zoom_matches + base64_matches

        if not dry_run:
            filepath.write_text(normalized_content, encoding='utf-8')
            print(f"✓ Updated {filepath} ({num_replacements} images normalized)")
        else:
            print(f"[DRY RUN] Would update {filepath} ({num_replacements} images)")

        return True, num_replacements

    except Exception as e:
        print(f"✗ Error processing {filepath}: {e}", file=sys.stderr)
        return False, 0


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='Normalize Slack emoji and Zoom speaker images in markdown files',
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

  # Also normalize whitespace (collapse blank lines, trim trailing spaces)
  %(prog)s --normalize-whitespace /path/to/file.md
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

    parser.add_argument(
        '--normalize-whitespace',
        action='store_true',
        help='Also normalize whitespace (collapse blank lines, trim trailing spaces)'
    )

    args = parser.parse_args()

    # Load whitespace normalizer if requested
    normalize_function = None
    if args.normalize_whitespace:
        from normalize_whitespaces import normalize_whitespace
        normalize_function = normalize_whitespace

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
        changed, num_replacements = process_file(filepath, args.dry_run, normalize_function)

        if changed:
            total_changed += 1
            total_replacements += num_replacements

    print(f"\n{'[DRY RUN] ' if args.dry_run else ''}Summary: {total_changed}/{total_files} files modified, {total_replacements} images normalized")

    return 0 if total_files > 0 else 1


if __name__ == '__main__':
    sys.exit(main())
