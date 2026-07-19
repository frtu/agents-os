#!/usr/bin/env python3
"""CLI entry point for voice_memo module."""

import argparse
import json
import sys
from pathlib import Path

from . import AudioMetadata, VoiceMemoHelper, DEFAULT_RECORDINGS_DIR


def main():
    parser = argparse.ArgumentParser(description="Voice Memo Helper")
    subparsers = parser.add_subparsers(dest="command", required=True, help="Command to run")

    # list command
    list_parser = subparsers.add_parser("list", help="List recordings")
    list_parser.add_argument(
        "--limit", "-n", type=int, default=5,
        help="Number of recordings to list (default: 5)"
    )
    list_parser.add_argument(
        "--dir", "-d", type=str, default=None,
        help="Recordings directory"
    )
    list_parser.add_argument(
        "--name", type=str, default=None,
        help="Filter by title (case-insensitive substring match, or 'latest')"
    )

    # metadata command
    meta_parser = subparsers.add_parser("metadata", help="Get audio file metadata")
    meta_parser.add_argument("file", type=str, help="Path to audio file")
    meta_parser.add_argument("--json", action="store_true", help="Output as JSON")

    args = parser.parse_args()

    if args.command == "list":
        recordings_dir = Path(args.dir) if args.dir else DEFAULT_RECORDINGS_DIR
        helper = VoiceMemoHelper(recordings_dir)

        recordings = helper.list_recordings(limit=None if args.name else args.limit)

        if args.name:
            if args.name.lower() == "latest" and recordings:
                recordings = [recordings[0]]
            else:
                recordings = [(t, p) for t, p in recordings if helper.match_name(t, args.name)]
                if args.limit:
                    recordings = recordings[:args.limit]

        if not recordings:
            print("No recordings found.", file=sys.stderr)
            sys.exit(1)

        for title, path in recordings:
            print(f"{title};{path}")

    elif args.command == "metadata":
        filepath = Path(args.file)
        if not filepath.exists():
            print(f"File not found: {filepath}", file=sys.stderr)
            sys.exit(1)

        helper = VoiceMemoHelper()
        meta = helper.get_metadata(filepath)

        if args.json:
            print(json.dumps({
                "path": str(meta.path),
                "title": meta.title,
                "duration_seconds": meta.duration_seconds,
                "bitrate_kbps": meta.bitrate_kbps,
                "file_size_bytes": meta.file_size_bytes,
                "sample_rate_hz": meta.sample_rate_hz,
                "channels": meta.channels,
                "codec": meta.codec,
            }))
        else:
            print(f"title:{meta.title}")
            print(f"duration:{meta.duration_seconds or 'unknown'}")
            print(f"bitrate:{meta.bitrate_kbps or 'unknown'}")
            print(f"file_size:{meta.file_size_bytes or 'unknown'}")
            print(f"sample_rate:{meta.sample_rate_hz or 'unknown'}")
            print(f"channels:{meta.channels or 'unknown'}")
            print(f"codec:{meta.codec or 'unknown'}")


if __name__ == "__main__":
    main()
