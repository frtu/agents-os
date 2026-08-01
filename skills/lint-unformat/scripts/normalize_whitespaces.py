#!/usr/bin/env python3
"""
Utility functions for whitespace normalization and code block formatting.
"""

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
