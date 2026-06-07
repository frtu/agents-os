#!/usr/bin/env python3
"""
Fix unescaped wikilinks in markdown tables.

Scans all .md files and ensures wikilinks inside table rows (lines starting with |)
use escaped pipes: [[link\\|name]] instead of [[link|name]].
"""

import re
import sys
from pathlib import Path

# Regex to find wikilinks with unescaped pipe inside
# Matches [[...]] containing | that is NOT preceded by \
UNESCAPED_WIKILINK = re.compile(r'\[\[([^\]|]+)(?<!\\)\|([^\]]+)\]\]')


def fix_wikilinks_in_line(line: str) -> str:
    """Fix unescaped wikilinks in a single line."""
    def escape_pipe(match):
        link = match.group(1)
        name = match.group(2)
        return f'[[{link}\\|{name}]]'

    return UNESCAPED_WIKILINK.sub(escape_pipe, line)


def process_file(filepath: Path, dry_run: bool = False) -> list[tuple[int, str, str]]:
    """
    Process a single file and fix table wikilinks.

    Returns list of (line_number, old_line, new_line) for changes made.
    """
    changes = []

    try:
        content = filepath.read_text(encoding='utf-8')
    except Exception as e:
        print(f"  Error reading {filepath}: {e}", file=sys.stderr)
        return changes

    lines = content.split('\n')
    modified = False

    for i, line in enumerate(lines):
        # Only process table rows (lines starting with |)
        if not line.strip().startswith('|'):
            continue

        # Check if line has any wikilinks
        if '[[' not in line:
            continue

        new_line = fix_wikilinks_in_line(line)

        if new_line != line:
            changes.append((i + 1, line, new_line))
            lines[i] = new_line
            modified = True

    if modified and not dry_run:
        filepath.write_text('\n'.join(lines), encoding='utf-8')

    return changes


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Fix unescaped wikilinks in markdown tables')
    parser.add_argument('path', nargs='?', default='.', help='Directory or file to process')
    parser.add_argument('--dry-run', '-n', action='store_true', help='Show changes without modifying files')
    parser.add_argument('--verbose', '-v', action='store_true', help='Show all changes')
    args = parser.parse_args()

    path = Path(args.path)

    if path.is_file():
        files = [path]
    else:
        files = sorted(path.rglob('*.md'))

    total_changes = 0
    files_changed = 0

    for filepath in files:
        # Skip raw/ directory (immutable sources)
        if 'raw/' in str(filepath) or '/raw/' in str(filepath):
            continue

        changes = process_file(filepath, dry_run=args.dry_run)

        if changes:
            files_changed += 1
            total_changes += len(changes)

            print(f"\n{filepath}:")
            for line_num, old, new in changes:
                if args.verbose:
                    print(f"  L{line_num}:")
                    print(f"    - {old.strip()}")
                    print(f"    + {new.strip()}")
                else:
                    # Extract just the wikilink that changed
                    print(f"  L{line_num}: fixed wikilink escape")

    # Summary
    action = "Would fix" if args.dry_run else "Fixed"
    print(f"\n{action} {total_changes} wikilink(s) in {files_changed} file(s)")

    if args.dry_run and total_changes > 0:
        print("Run without --dry-run to apply changes")


if __name__ == '__main__':
    main()
