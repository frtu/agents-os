#!/usr/bin/env python3
"""Voice Memo helper: list recordings, extract metadata, evaluate MPS risk."""

import argparse
import json
import os
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

DEFAULT_RECORDINGS_DIR = Path.home() / "Library/Group Containers/group.com.apple.VoiceMemos.shared/Recordings"


@dataclass
class AudioMetadata:
    """Metadata extracted from an audio file."""
    path: Path
    title: str
    duration_seconds: Optional[int] = None
    bitrate_kbps: Optional[int] = None


@dataclass
class MPSRiskResult:
    """Result of MPS failure risk evaluation."""
    level: str  # low, moderate, high, critical
    score: int
    reasons: list[str]

    def should_use_cpu(self) -> bool:
        return self.level in ("high", "critical")


class VoiceMemoHelper:
    """Helper class for Voice Memo operations and MPS risk evaluation."""

    # MPS risk thresholds (empirically calibrated)
    MPS_SAFE_DURATION = 1500      # 25 min - low risk
    MPS_WARN_DURATION = 1800      # 30 min - high risk
    MPS_FAILURE_WINDOW = 3600    # 1 hour
    MPS_MIN_GPU_FREE_MB = 2048
    HIGH_BITRATE_THRESHOLD = 256  # kbps

    def __init__(self, recordings_dir: Optional[Path] = None, failure_log_path: Optional[Path] = None):
        self.recordings_dir = recordings_dir or DEFAULT_RECORDINGS_DIR
        self.failure_log_path = failure_log_path

    def get_title(self, filepath: Path) -> str:
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

    def get_duration(self, filepath: Path) -> Optional[int]:
        """Get audio duration in seconds using ffprobe."""
        try:
            result = subprocess.run(
                [
                    "ffprobe", "-v", "quiet",
                    "-show_entries", "format=duration",
                    "-of", "csv=p=0", str(filepath)
                ],
                capture_output=True,
                text=True,
            )
            if result.stdout.strip():
                return int(float(result.stdout.strip()))
        except Exception:
            pass
        return None

    def get_bitrate(self, filepath: Path) -> Optional[int]:
        """Get audio bitrate in kbps using ffprobe."""
        try:
            result = subprocess.run(
                [
                    "ffprobe", "-v", "quiet",
                    "-show_entries", "format=bit_rate",
                    "-of", "csv=p=0", str(filepath)
                ],
                capture_output=True,
                text=True,
            )
            if result.stdout.strip():
                return int(result.stdout.strip()) // 1000
        except Exception:
            pass
        return None

    def get_metadata(self, filepath: Path) -> AudioMetadata:
        """Get full metadata for an audio file."""
        return AudioMetadata(
            path=filepath,
            title=self.get_title(filepath),
            duration_seconds=self.get_duration(filepath),
            bitrate_kbps=self.get_bitrate(filepath),
        )

    def list_recordings(self, limit: Optional[int] = None) -> list[tuple[str, str]]:
        """List recordings sorted by modification time (newest first)."""
        if not self.recordings_dir.exists():
            return []

        m4a_files = list(self.recordings_dir.glob("*.m4a"))
        m4a_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)

        if limit:
            m4a_files = m4a_files[:limit]

        return [(self.get_title(f), str(f)) for f in m4a_files]

    def match_name(self, title: str, pattern: str) -> bool:
        """Check if title matches pattern (case-insensitive, supports 'latest')."""
        if pattern.lower() == "latest":
            return True
        return pattern.lower() in title.lower()

    def has_recent_mps_failure(self) -> bool:
        """Check if MPS failed recently (within failure window)."""
        if not self.failure_log_path or not self.failure_log_path.exists():
            return False

        now = int(time.time())
        cutoff = now - self.MPS_FAILURE_WINDOW

        try:
            with open(self.failure_log_path) as f:
                for line in f:
                    line = line.strip()
                    if line and int(line) > cutoff:
                        return True
        except Exception:
            pass
        return False

    def record_mps_failure(self) -> None:
        """Record an MPS failure timestamp."""
        if not self.failure_log_path:
            return

        try:
            timestamps = []
            if self.failure_log_path.exists():
                with open(self.failure_log_path) as f:
                    timestamps = [line.strip() for line in f if line.strip()]

            timestamps.append(str(int(time.time())))
            timestamps = timestamps[-10:]  # Keep last 10

            with open(self.failure_log_path, "w") as f:
                f.write("\n".join(timestamps) + "\n")
        except Exception:
            pass

    def get_gpu_free_mb(self) -> Optional[int]:
        """Get approximate free GPU memory (macOS unified memory)."""
        try:
            result = subprocess.run(
                ["vm_stat"],
                capture_output=True,
                text=True,
            )
            free_pages = 0
            inactive_pages = 0
            for line in result.stdout.splitlines():
                if "Pages free" in line:
                    free_pages = int(line.split()[-1].rstrip("."))
                elif "Pages inactive" in line:
                    inactive_pages = int(line.split()[-1].rstrip("."))

            if free_pages or inactive_pages:
                # Page size is 16384 bytes on Apple Silicon
                return (free_pages + inactive_pages) * 16384 // 1024 // 1024
        except Exception:
            pass
        return None

    def evaluate_mps_risk(
        self,
        duration: Optional[int] = None,
        bitrate: Optional[int] = None,
    ) -> MPSRiskResult:
        """Evaluate MPS failure risk based on multiple factors."""
        score = 0
        reasons = []

        # Factor 1: Duration
        if duration is not None:
            if duration > self.MPS_WARN_DURATION:
                score += 40
                reasons.append(f"duration>{self.MPS_WARN_DURATION}s")
            elif duration > self.MPS_SAFE_DURATION:
                score += 20
                reasons.append(f"duration>{self.MPS_SAFE_DURATION}s")

        # Factor 2: Recent failures
        if self.has_recent_mps_failure():
            score += 30
            reasons.append("recent_failure")

        # Factor 3: GPU memory
        gpu_free = self.get_gpu_free_mb()
        if gpu_free is not None and gpu_free < self.MPS_MIN_GPU_FREE_MB:
            score += 25
            reasons.append(f"low_memory:{gpu_free}MB")

        # Factor 4: High bitrate
        if bitrate is not None and bitrate > self.HIGH_BITRATE_THRESHOLD:
            score += 10
            reasons.append(f"high_bitrate:{bitrate}kbps")

        # Determine level
        if score >= 50:
            level = "critical"
        elif score >= 30:
            level = "high"
        elif score >= 15:
            level = "moderate"
        else:
            level = "low"

        return MPSRiskResult(level=level, score=score, reasons=reasons)

    def evaluate_mps_risk_for_file(self, filepath: Path) -> MPSRiskResult:
        """Evaluate MPS risk for a specific audio file."""
        duration = self.get_duration(filepath)
        bitrate = self.get_bitrate(filepath)
        return self.evaluate_mps_risk(duration, bitrate)


def main():
    # Check for backward-compatible invocation (no subcommand, just flags)
    # Old style: list_recordings.py --name "Jan-Khoi"
    # New style: list_recordings.py list --name "Jan-Khoi"
    if len(sys.argv) == 1 or (len(sys.argv) > 1 and sys.argv[1].startswith("-")):
        # Old-style invocation - treat as "list" command
        parser = argparse.ArgumentParser(description="List Voice Memos")
        parser.add_argument(
            "--limit", "-n", type=int, default=5,
            help="Number of recordings to list (default: 5)"
        )
        parser.add_argument(
            "--dir", "-d", type=str, default=None,
            help="Recordings directory"
        )
        parser.add_argument(
            "--name", type=str, default=None,
            help="Filter by title (case-insensitive substring match, or 'latest')"
        )
        args = parser.parse_args()
        args.command = "list"
    else:
        # New-style with subcommands
        parser = argparse.ArgumentParser(description="Voice Memo Helper")
        subparsers = parser.add_subparsers(dest="command", help="Command to run")

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

        # risk command
        risk_parser = subparsers.add_parser("risk", help="Evaluate MPS risk for a file")
        risk_parser.add_argument("file", type=str, help="Path to audio file")
        risk_parser.add_argument(
            "--failure-log", type=str, default=None,
            help="Path to MPS failure log file"
        )

        # record-failure command
        fail_parser = subparsers.add_parser("record-failure", help="Record an MPS failure")
        fail_parser.add_argument(
            "--failure-log", type=str, required=True,
            help="Path to MPS failure log file"
        )

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
            }))
        else:
            print(f"title:{meta.title}")
            print(f"duration:{meta.duration_seconds or 'unknown'}")
            print(f"bitrate:{meta.bitrate_kbps or 'unknown'}")

    elif args.command == "risk":
        filepath = Path(args.file)
        if not filepath.exists():
            print(f"File not found: {filepath}", file=sys.stderr)
            sys.exit(1)

        failure_log = Path(args.failure_log) if args.failure_log else None
        helper = VoiceMemoHelper(failure_log_path=failure_log)

        meta = helper.get_metadata(filepath)
        risk = helper.evaluate_mps_risk(meta.duration_seconds, meta.bitrate_kbps)

        print(f"level:{risk.level}")
        print(f"score:{risk.score}")
        print(f"use_cpu:{1 if risk.should_use_cpu() else 0}")
        print(f"reasons:{','.join(risk.reasons) if risk.reasons else 'none'}")
        print(f"duration:{meta.duration_seconds or 'unknown'}")
        print(f"bitrate:{meta.bitrate_kbps or 'unknown'}")

    elif args.command == "record-failure":
        failure_log = Path(args.failure_log)
        helper = VoiceMemoHelper(failure_log_path=failure_log)
        helper.record_mps_failure()
        print("Recorded MPS failure")


if __name__ == "__main__":
    main()
