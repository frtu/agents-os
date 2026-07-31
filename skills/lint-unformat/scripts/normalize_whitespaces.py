#!/usr/bin/env python3
"""
Utility functions for whitespace normalization and code block formatting.
"""

import sys
from pathlib import Path


def normalize_whitespace(content: str) -> str:
    """
    Clean up whitespace issues common in Slack exports.

    Fixes:
    1. Remove trailing whitespace from blank lines (lines that are only whitespace)
    2. Preserve trailing double-space on content lines (Slack line break syntax)
    3. Collapse multiple consecutive blank lines into single blank line
    4. Remove blank lines immediately after section headers (lines not starting with list/code markers)
    5. Ensure file ends with exactly one newline

    Args:
        content: Text content to normalize

    Returns:
        Normalized text with cleaned whitespace
    """
    lines = content.splitlines()
    result = []
    prev_blank = False
    i = 0

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        is_blank = len(stripped) == 0

        if is_blank:
            # Blank line: skip if previous was blank
            if not prev_blank:
                # Check if next line is a list item (starts with -)
                # If current line is blank and next is list item, skip it (blank after header)
                if (i + 1 < len(lines) and
                    lines[i + 1].lstrip().startswith('-')):
                    i += 1
                    continue
                result.append('')
                prev_blank = True
            i += 1
        else:
            # Content line: preserve trailing double-space (Slack line break)
            if line.endswith('  '):
                result.append(line.rstrip() + '  ')
            else:
                result.append(line.rstrip())
            prev_blank = False
            i += 1

    # Join and ensure single trailing newline
    return '\n'.join(result) + '\n'


def normalize_whitespace_in_code_blocks(content: str) -> str:
    """
    Remove unnecessary blank lines inside markdown code blocks.

    Processes content and removes blank lines that appear between
    triple backticks (```), keeping the code blocks intact.

    Args:
        content: File content with potential code blocks

    Returns:
        Content with blank lines removed from inside code blocks
    """
    result = []
    in_code_block = False

    for line in content.splitlines(keepends=True):
        if line.strip().startswith('```'):
            in_code_block = not in_code_block
            result.append(line)
        elif in_code_block and line.strip() == '':
            # Skip blank lines inside code blocks
            continue
        else:
            result.append(line)

    return ''.join(result)


def process_file(filepath: Path, dry_run: bool = False) -> tuple[bool, str]:
    """
    Process a single file to remove blank lines in code blocks.

    Args:
        filepath: Path to the file to process
        dry_run: If True, don't write changes, just show what would happen

    Returns:
        Tuple of (file_was_changed, operation_message)
    """
    try:
        original_content = filepath.read_text(encoding='utf-8')
        processed_content = normalize_whitespace_in_code_blocks(original_content)

        if original_content == processed_content:
            return False, f"No changes needed for {filepath}"

        if not dry_run:
            filepath.write_text(processed_content, encoding='utf-8')
            return True, f"✓ Updated {filepath}"
        else:
            return True, f"[DRY RUN] Would update {filepath}"

    except Exception as e:
        return False, f"✗ Error processing {filepath}: {e}"


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='Remove blank lines inside markdown code blocks',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process a single file
  %(prog)s /path/to/file.md

  # Process multiple files
  %(prog)s file1.md file2.md file3.md

  # Dry run (preview changes)
  %(prog)s --dry-run /path/to/file.md
        """
    )

    parser.add_argument(
        'files',
        nargs='+',
        type=Path,
        help='File(s) to process'
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be changed without modifying files'
    )

    args = parser.parse_args()

    total_files = 0
    total_changed = 0

    for filepath in args.files:
        if not filepath.exists():
            print(f"✗ File not found: {filepath}", file=sys.stderr)
            continue

        if not filepath.is_file():
            print(f"✗ Not a file: {filepath}", file=sys.stderr)
            continue

        total_files += 1
        changed, message = process_file(filepath, args.dry_run)
        print(message)

        if changed:
            total_changed += 1

    print(f"\n{'[DRY RUN] ' if args.dry_run else ''}Summary: {total_changed}/{total_files} files processed")

    return 0 if total_files > 0 else 1


if __name__ == '__main__':
    sys.exit(main())
