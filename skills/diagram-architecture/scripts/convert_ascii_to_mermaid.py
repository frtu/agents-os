#!/usr/bin/env python3
"""
Convert ASCII art diagrams to Mermaid diagrams while preserving layout orientation.

Detects diagram types:
- Vertical flows (↓) → flowchart TD
- Horizontal flows (→) → flowchart LR
- Tree structures (│├└) → flowchart TD with tree layout
"""

import re
from pathlib import Path
from typing import Tuple, List


def detect_diagram_type(block: str) -> Tuple[str, str]:
    """
    Detect diagram type and orientation.

    Returns:
        (diagram_type, orientation)
        - diagram_type: 'vertical_flow', 'horizontal_flow', 'tree'
        - orientation: 'TD' (vertical) or 'LR' (horizontal)
    """
    has_vertical_arrow = '↓' in block
    has_horizontal_arrow = '→' in block
    has_tree_chars = any(c in block for c in ['│', '├', '└', '─'])

    if has_tree_chars:
        return 'tree', 'TD'
    elif has_horizontal_arrow:
        return 'horizontal_flow', 'LR'
    elif has_vertical_arrow:
        return 'vertical_flow', 'TD'

    # Default based on most common in codebase
    return 'vertical_flow', 'TD'


def parse_vertical_flow(block: str) -> List[str]:
    """Parse vertical flow diagram (↓) into list of items."""
    items = []
    for line in block.strip().split('\n'):
        line = line.strip()
        if line and line != '↓':
            items.append(line)
    return items


def parse_horizontal_flow(block: str) -> List[str]:
    """Parse horizontal flow diagram (→) into list of items."""
    # Handle both single-line and multi-line formats
    if '→' in block and '\n' not in block.replace('\n→\n', '\n'):
        # Single line with arrows: "A → B → C"
        items = [item.strip() for item in block.split('→') if item.strip()]
    else:
        # Multi-line format
        items = []
        for line in block.strip().split('\n'):
            line = line.strip()
            if line and line != '→':
                items.append(line)
    return items


def parse_tree_structure(block: str) -> List[Tuple[str, int]]:
    """
    Parse tree diagram into (text, indent_level) tuples.

    Returns list of (text, depth) where depth indicates tree level.
    """
    items = []
    lines = block.strip().split('\n')

    for line in lines:
        # Count leading whitespace/tree chars
        match = re.match(r'^([\s│├└─]*)', line)
        indent = len(match.group(1)) if match else 0

        # Extract text (remove tree characters)
        text = re.sub(r'^[\s│├└─]+', '', line).strip()

        if text:
            # Determine depth based on tree characters
            depth = line.count('│') + line.count('├') + line.count('└')
            depth = max(1, depth // 2) if depth > 0 else 0
            items.append((text, depth))

    return items


def escape_mermaid_label(text: str) -> str:
    """Escape special characters in Mermaid node labels.

    Parentheses and other special chars need quotes around the label.
    """
    special_chars = {'(', ')', '[', ']', '{', '}', '#', '&', '<', '>'}
    if any(char in text for char in special_chars):
        # Use quotes to escape special characters
        return f'["{text}"]'
    return f'[{text}]'


def items_to_mermaid_flow(items: List[str], orientation: str = 'TD') -> str:
    """Convert list of items to Mermaid flowchart."""
    if not items:
        return ""

    # Create node IDs and labels
    nodes = []
    connections = []

    for i, item in enumerate(items):
        node_id = f"N{i}"
        label = escape_mermaid_label(item)

        nodes.append(f'    {node_id}{label}')

        # Connect to previous node
        if i > 0:
            connections.append(f'    N{i-1} --> {node_id}')

    result = f'flowchart {orientation}\n'
    result += '\n'.join(nodes)
    if connections:
        result += '\n' + '\n'.join(connections)

    return result


def tree_to_mermaid(items: List[Tuple[str, int]], orientation: str = 'TD') -> str:
    """Convert tree structure to Mermaid flowchart with subgraphs."""
    if not items:
        return ""

    # Group by depth
    by_depth = {}
    for text, depth in items:
        if depth not in by_depth:
            by_depth[depth] = []
        by_depth[depth].append(text)

    result = f'flowchart {orientation}\n'

    # Generate nodes and connections based on structure
    node_map = {}
    prev_node = None

    for i, (text, depth) in enumerate(items):
        node_id = f"N{i}"
        node_map[(text, depth)] = node_id

        # Format label with escaping
        label = escape_mermaid_label(text)
        result += f'    {node_id}{label}\n'

        # Connect to previous item at same or lesser depth
        if prev_node and depth > 0:
            result += f'    N{prev_node} --> {node_id}\n'

        prev_node = i

    return result.rstrip()


def vertical_flow_to_mermaid(block: str) -> str:
    """Convert vertical ASCII flow to Mermaid TD flowchart."""
    items = parse_vertical_flow(block)
    return items_to_mermaid_flow(items, 'TD')


def horizontal_flow_to_mermaid(block: str) -> str:
    """Convert horizontal ASCII flow to Mermaid LR flowchart."""
    items = parse_horizontal_flow(block)
    return items_to_mermaid_flow(items, 'LR')


def tree_to_mermaid_flowchart(block: str) -> str:
    """Convert tree ASCII structure to Mermaid flowchart."""
    items = parse_tree_structure(block)
    return tree_to_mermaid(items, 'TD')


def ascii_to_mermaid(block: str) -> str:
    """Convert ASCII diagram to Mermaid format, preserving orientation."""
    diagram_type, orientation = detect_diagram_type(block)

    if diagram_type == 'horizontal_flow':
        return horizontal_flow_to_mermaid(block)
    elif diagram_type == 'tree':
        return tree_to_mermaid_flowchart(block)
    else:  # vertical_flow
        return vertical_flow_to_mermaid(block)


def is_ascii_diagram(block: str) -> bool:
    """Check if a code block is an ASCII diagram that should be converted.

    Skips blocks containing box-drawing characters used for UI mockups,
    tables, or complex ASCII art that don't convert well to Mermaid.
    """
    # Box-drawing characters indicate UI mockups - skip these
    box_drawing_chars = {'┌', '┐', '┘', '┬', '┴', '┼', '┤', '├'}
    if any(char in block for char in box_drawing_chars):
        return False

    # Only convert blocks with simple flow arrows
    simple_flow_chars = {'↓', '→'}
    return any(char in block for char in simple_flow_chars)


def process_file(filepath: Path, dry_run: bool = False) -> Tuple[bool, int]:
    """
    Convert ASCII diagrams in file to Mermaid format.

    Returns:
        (file_changed, num_diagrams_converted)
    """
    content = filepath.read_text(encoding='utf-8')
    original_content = content

    # Find all code blocks - handles both ``` and ```language formats
    code_block_pattern = r'```(?:[a-z]+)?\n(.*?)\n```'
    num_converted = 0

    def replace_with_mermaid(match):
        nonlocal num_converted
        ascii_block = match.group(1)
        full_match = match.group(0)

        # Check if this is an ASCII diagram
        if not is_ascii_diagram(ascii_block):
            return full_match  # Return unchanged

        num_converted += 1
        mermaid_code = ascii_to_mermaid(ascii_block)
        return f'```mermaid\n{mermaid_code}\n```'

    content = re.sub(code_block_pattern, replace_with_mermaid, content, flags=re.DOTALL)

    if content == original_content:
        return False, 0

    if not dry_run:
        filepath.write_text(content, encoding='utf-8')

    return True, num_converted


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='Convert ASCII diagrams to Mermaid format',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Convert single file
  %(prog)s /path/to/file.md

  # Dry run to preview
  %(prog)s --dry-run /path/to/file.md

  # Convert multiple files
  %(prog)s file1.md file2.md
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
        help='Preview changes without modifying files'
    )

    args = parser.parse_args()

    total_files = 0
    total_changed = 0
    total_diagrams = 0

    for filepath in args.files:
        if not filepath.exists():
            print(f"✗ File not found: {filepath}")
            continue

        total_files += 1
        changed, num_diagrams = process_file(filepath, args.dry_run)

        if changed:
            total_changed += 1
            total_diagrams += num_diagrams
            status = "[DRY RUN] Would convert" if args.dry_run else "✓ Converted"
            print(f"{status} {filepath} ({num_diagrams} diagrams)")
        else:
            print(f"No diagrams found in {filepath}")

    print(f"\n{'[DRY RUN] ' if args.dry_run else ''}Summary: {total_diagrams} diagrams converted in {total_changed}/{total_files} files")

    return 0 if total_files > 0 else 1


if __name__ == '__main__':
    import sys
    sys.exit(main())
