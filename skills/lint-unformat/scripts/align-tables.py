#!/usr/bin/env python3
"""
Normalize and vertically align markdown tables.

Scans .md files, finds GitHub-style tables (consecutive lines starting with |
followed by a separator row), and pads every column to the width of its widest
cell so the pipes line up vertically. Respects per-column alignment declared in
the separator row (:---, ---:, :---:). Escaped pipes (\\|), as used inside
wikilinks, are treated as literal text and do not split cells.
"""

import re
import sys
import unicodedata
from pathlib import Path

SEPARATOR_CELL = re.compile(r'^:?-+:?$')
# Split a row on pipes that are not escaped with a backslash
CELL_SPLIT = re.compile(r'(?<!\\)\|')


def display_width(s: str) -> int:
    """Visual width of a string, counting wide/fullwidth chars as 2."""
    width = 0
    for ch in s:
        width += 2 if unicodedata.east_asian_width(ch) in ('W', 'F') else 1
    return width


def pad(s: str, width: int, align: str) -> str:
    diff = width - display_width(s)
    if diff <= 0:
        return s
    if align == 'right':
        return ' ' * diff + s
    if align == 'center':
        left = diff // 2
        return ' ' * left + s + ' ' * (diff - left)
    return s + ' ' * diff


def split_row(line: str) -> list[str]:
    stripped = line.strip()
    if stripped.startswith('|'):
        stripped = stripped[1:]
    if stripped.endswith('|'):
        stripped = stripped[:-1]
    return [c.strip() for c in CELL_SPLIT.split(stripped)]


def is_table_row(line: str) -> bool:
    return line.strip().startswith('|')


def is_separator_row(cells: list[str]) -> bool:
    return len(cells) > 0 and all(SEPARATOR_CELL.match(c) for c in cells)


def alignments_from_separator(cells: list[str]) -> list[str]:
    aligns = []
    for c in cells:
        left = c.startswith(':')
        right = c.endswith(':')
        if left and right:
            aligns.append('center')
        elif right:
            aligns.append('right')
        elif left:
            aligns.append('left')
        else:
            aligns.append('none')
    return aligns


def separator_cell(width: int, align: str) -> str:
    if align == 'center':
        return ':' + '-' * (width - 2) + ':'
    if align == 'right':
        return '-' * (width - 1) + ':'
    if align == 'left':
        return ':' + '-' * (width - 1)
    return '-' * width


def format_table(rows: list[list[str]], sep_index: int) -> list[str]:
    """Render a parsed table (list of cell-lists) as aligned lines."""
    aligns = alignments_from_separator(rows[sep_index])
    ncols = max(len(r) for r in rows)
    aligns += ['none'] * (ncols - len(aligns))

    # Column width = widest non-separator cell, min 3 for a readable separator.
    widths = [3] * ncols
    for i, row in enumerate(rows):
        if i == sep_index:
            continue
        for c, cell in enumerate(row):
            widths[c] = max(widths[c], display_width(cell))

    out = []
    for i, row in enumerate(rows):
        cells = row + [''] * (ncols - len(row))
        if i == sep_index:
            rendered = [separator_cell(widths[c], aligns[c]) for c in range(ncols)]
        else:
            align = ['left' if a == 'none' else a for a in aligns]
            rendered = [pad(cells[c], widths[c], align[c]) for c in range(ncols)]
        out.append('| ' + ' | '.join(rendered) + ' |')
    return out


def process_file(filepath: Path, dry_run: bool = False) -> list[tuple[int, int]]:
    """Reformat tables in a file. Returns list of (start_line, end_line) changed."""
    try:
        content = filepath.read_text(encoding='utf-8')
    except Exception as e:
        print(f"  Error reading {filepath}: {e}", file=sys.stderr)
        return []

    lines = content.split('\n')
    out_lines: list[str] = []
    changed_blocks: list[tuple[int, int]] = []
    i = 0
    n = len(lines)

    while i < n:
        if not is_table_row(lines[i]):
            out_lines.append(lines[i])
            i += 1
            continue

        # Gather a contiguous block of table rows.
        start = i
        block = []
        while i < n and is_table_row(lines[i]):
            block.append(lines[i])
            i += 1

        parsed = [split_row(l) for l in block]

        # A valid table needs a separator as its 2nd row.
        if len(parsed) >= 2 and is_separator_row(parsed[1]):
            formatted = format_table(parsed, sep_index=1)
            if formatted != block:
                changed_blocks.append((start + 1, start + len(block)))
            out_lines.extend(formatted)
        else:
            out_lines.extend(block)

    if changed_blocks and not dry_run:
        filepath.write_text('\n'.join(out_lines), encoding='utf-8')

    return changed_blocks


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Normalize and vertically align markdown tables')
    parser.add_argument('path', nargs='?', default='.', help='Directory or file to process')
    parser.add_argument('--dry-run', '-n', action='store_true', help='Show changes without modifying files')
    parser.add_argument('--verbose', '-v', action='store_true', help='Show each reformatted table block')
    args = parser.parse_args()

    path = Path(args.path)
    files = [path] if path.is_file() else sorted(path.rglob('*.md'))

    total_tables = 0
    files_changed = 0

    for filepath in files:
        # Skip raw/ directory (immutable sources)
        if 'raw/' in str(filepath) or '/raw/' in str(filepath):
            continue

        blocks = process_file(filepath, dry_run=args.dry_run)
        if blocks:
            files_changed += 1
            total_tables += len(blocks)
            print(f"\n{filepath}:")
            for start, end in blocks:
                if args.verbose:
                    print(f"  L{start}-{end}: aligned table")
                else:
                    print(f"  L{start}: aligned table")

    action = "Would align" if args.dry_run else "Aligned"
    print(f"\n{action} {total_tables} table(s) in {files_changed} file(s)")

    if args.dry_run and total_tables > 0:
        print("Run without --dry-run to apply changes")


if __name__ == '__main__':
    main()
