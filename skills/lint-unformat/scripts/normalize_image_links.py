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

