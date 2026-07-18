#!/usr/bin/env python3
"""List Voice Memos as CSV: title;path, sorted newest to oldest."""

import argparse
import json
import subprocess
import sys
from pathlib import Path

DEFAULT_RECORDINGS_DIR = Path.home() / "Library/Group Containers/group.com.apple.VoiceMemos.shared/Recordings"


def get_title(filepath: Path) -> str:
    """Extract title from m4a metadata using ffprobe, fallback to filename."""
    try:
        result = subprocess.run(
            [
                "ffprobe", "-v", "quiet", "-print_format", "json",
                "-show_entries", "format_tags=title", str(filepath)
            ],
            capture_output=True,
            text=True,
        )
        data = json.loads(result.stdout)
        title = data.get("format", {}).get("tags", {}).get("title")
        if title:
            return title
    except Exception:
        pass
    return filepath.stem


def list_recordings(recordings_dir: Path, limit: int = None) -> list:
    """List recordings sorted by modification time (newest first)."""
    if not recordings_dir.exists():
        print(f"Directory not found: {recordings_dir}", file=sys.stderr)
        return []

    m4a_files = list(recordings_dir.glob("*.m4a"))

    # Sort by modification time, newest first
    m4a_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)

    if limit:
        m4a_files = m4a_files[:limit]

    results = []
    for filepath in m4a_files:
        title = get_title(filepath)
        results.append((title, str(filepath)))

    return results


def match_name(title: str, pattern: str) -> bool:
    """Check if title matches pattern (case-insensitive, supports 'latest')."""
    if pattern.lower() == "latest":
        return True
    return pattern.lower() in title.lower()


def main():
    parser = argparse.ArgumentParser(description="List Voice Memos")
    parser.add_argument(
        "--limit", "-n", type=int, default=5,
        help="Number of recordings to list (default: 5)"
    )
    parser.add_argument(
        "--dir", "-d", type=str, default=None,
        help="Recordings directory (default: Voice Memos folder)"
    )
    parser.add_argument(
        "--name", type=str, default=None,
        help="Filter by title (case-insensitive substring match, or 'latest' for newest)"
    )
    args = parser.parse_args()

    recordings_dir = Path(args.dir) if args.dir else DEFAULT_RECORDINGS_DIR

    recordings = list_recordings(recordings_dir, limit=None if args.name else args.limit)

    if args.name:
        if args.name.lower() == "latest" and recordings:
            recordings = [recordings[0]]
        else:
            recordings = [(t, p) for t, p in recordings if match_name(t, args.name)]
            if args.limit:
                recordings = recordings[:args.limit]

    if not recordings:
        print("No recordings found.", file=sys.stderr)
        sys.exit(1)

    for title, path in recordings:
        print(f"{title};{path}")


if __name__ == "__main__":
    main()
