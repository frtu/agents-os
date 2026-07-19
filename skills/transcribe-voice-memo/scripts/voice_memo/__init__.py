"""Voice Memo helper: list recordings and extract metadata."""

import json
import subprocess
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
    file_size_bytes: Optional[int] = None
    sample_rate_hz: Optional[int] = None
    channels: Optional[int] = None
    codec: Optional[str] = None


class VoiceMemoHelper:
    """Helper class for Voice Memo operations."""

    def __init__(self, recordings_dir: Optional[Path] = None):
        self.recordings_dir = recordings_dir or DEFAULT_RECORDINGS_DIR

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

    def get_file_size(self, filepath: Path) -> Optional[int]:
        """Get file size in bytes."""
        try:
            return filepath.stat().st_size
        except Exception:
            pass
        return None

    def get_sample_rate(self, filepath: Path) -> Optional[int]:
        """Get audio sample rate in Hz using ffprobe."""
        try:
            result = subprocess.run(
                [
                    "ffprobe", "-v", "quiet",
                    "-select_streams", "a:0",
                    "-show_entries", "stream=sample_rate",
                    "-of", "csv=p=0", str(filepath)
                ],
                capture_output=True,
                text=True,
            )
            if result.stdout.strip():
                return int(result.stdout.strip())
        except Exception:
            pass
        return None

    def get_channels(self, filepath: Path) -> Optional[int]:
        """Get number of audio channels using ffprobe."""
        try:
            result = subprocess.run(
                [
                    "ffprobe", "-v", "quiet",
                    "-select_streams", "a:0",
                    "-show_entries", "stream=channels",
                    "-of", "csv=p=0", str(filepath)
                ],
                capture_output=True,
                text=True,
            )
            if result.stdout.strip():
                return int(result.stdout.strip())
        except Exception:
            pass
        return None

    def get_codec(self, filepath: Path) -> Optional[str]:
        """Get audio codec name using ffprobe."""
        try:
            result = subprocess.run(
                [
                    "ffprobe", "-v", "quiet",
                    "-select_streams", "a:0",
                    "-show_entries", "stream=codec_name",
                    "-of", "csv=p=0", str(filepath)
                ],
                capture_output=True,
                text=True,
            )
            if result.stdout.strip():
                return result.stdout.strip()
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
            file_size_bytes=self.get_file_size(filepath),
            sample_rate_hz=self.get_sample_rate(filepath),
            channels=self.get_channels(filepath),
            codec=self.get_codec(filepath),
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
