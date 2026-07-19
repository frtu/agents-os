#!/usr/bin/env python3
"""Unit tests for VoiceMemoHelper class."""

import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from voice_memo import AudioMetadata, VoiceMemoHelper


class TestVoiceMemoHelperMetadata(unittest.TestCase):
    """Tests for metadata extraction methods."""

    def setUp(self):
        self.helper = VoiceMemoHelper()

    @patch("voice_memo.subprocess.run")
    def test_get_title_from_metadata(self, mock_run):
        mock_run.return_value = MagicMock(
            stdout='{"format": {"tags": {"title": "My Recording"}}}'
        )
        title = self.helper.get_title(Path("/fake/file.m4a"))
        self.assertEqual(title, "My Recording")

    @patch("voice_memo.subprocess.run")
    def test_get_title_fallback_to_filename(self, mock_run):
        mock_run.return_value = MagicMock(stdout='{"format": {}}')
        title = self.helper.get_title(Path("/fake/recording_2024.m4a"))
        self.assertEqual(title, "recording_2024")

    @patch("voice_memo.subprocess.run")
    def test_get_title_on_error(self, mock_run):
        mock_run.side_effect = Exception("ffprobe not found")
        title = self.helper.get_title(Path("/fake/fallback.m4a"))
        self.assertEqual(title, "fallback")

    @patch("voice_memo.subprocess.run")
    def test_get_duration_success(self, mock_run):
        mock_run.return_value = MagicMock(stdout="1234.56\n")
        duration = self.helper.get_duration(Path("/fake/file.m4a"))
        self.assertEqual(duration, 1234)

    @patch("voice_memo.subprocess.run")
    def test_get_duration_empty(self, mock_run):
        mock_run.return_value = MagicMock(stdout="")
        duration = self.helper.get_duration(Path("/fake/file.m4a"))
        self.assertIsNone(duration)

    @patch("voice_memo.subprocess.run")
    def test_get_duration_on_error(self, mock_run):
        mock_run.side_effect = Exception("ffprobe error")
        duration = self.helper.get_duration(Path("/fake/file.m4a"))
        self.assertIsNone(duration)

    @patch("voice_memo.subprocess.run")
    def test_get_bitrate_success(self, mock_run):
        mock_run.return_value = MagicMock(stdout="128000\n")
        bitrate = self.helper.get_bitrate(Path("/fake/file.m4a"))
        self.assertEqual(bitrate, 128)

    @patch("voice_memo.subprocess.run")
    def test_get_bitrate_on_error(self, mock_run):
        mock_run.side_effect = Exception("ffprobe error")
        bitrate = self.helper.get_bitrate(Path("/fake/file.m4a"))
        self.assertIsNone(bitrate)

    @patch.object(VoiceMemoHelper, "get_title", return_value="Test Recording")
    @patch.object(VoiceMemoHelper, "get_duration", return_value=300)
    @patch.object(VoiceMemoHelper, "get_bitrate", return_value=128)
    def test_get_metadata(self, mock_bitrate, mock_duration, mock_title):
        meta = self.helper.get_metadata(Path("/fake/file.m4a"))
        self.assertEqual(meta.title, "Test Recording")
        self.assertEqual(meta.duration_seconds, 300)
        self.assertEqual(meta.bitrate_kbps, 128)
        self.assertEqual(meta.path, Path("/fake/file.m4a"))


class TestVoiceMemoHelperListRecordings(unittest.TestCase):
    """Tests for list_recordings method."""

    def test_list_recordings_nonexistent_dir(self):
        helper = VoiceMemoHelper(recordings_dir=Path("/nonexistent/dir"))
        recordings = helper.list_recordings()
        self.assertEqual(recordings, [])

    def test_list_recordings_with_files(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)

            for i, name in enumerate(["old.m4a", "new.m4a", "middle.m4a"]):
                filepath = tmppath / name
                filepath.touch()
                import os
                os.utime(filepath, (time.time() - (100 - i * 50), time.time() - (100 - i * 50)))

            helper = VoiceMemoHelper(recordings_dir=tmppath)

            with patch.object(helper, "get_title", side_effect=lambda p: p.stem):
                recordings = helper.list_recordings()

            self.assertEqual(len(recordings), 3)
            self.assertEqual(recordings[0][0], "middle")  # newest
            self.assertEqual(recordings[2][0], "old")     # oldest

    def test_list_recordings_with_limit(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)

            for i in range(5):
                (tmppath / f"file{i}.m4a").touch()

            helper = VoiceMemoHelper(recordings_dir=tmppath)

            with patch.object(helper, "get_title", side_effect=lambda p: p.stem):
                recordings = helper.list_recordings(limit=2)

            self.assertEqual(len(recordings), 2)


class TestVoiceMemoHelperMatchName(unittest.TestCase):
    """Tests for match_name method."""

    def setUp(self):
        self.helper = VoiceMemoHelper()

    def test_match_latest(self):
        self.assertTrue(self.helper.match_name("Any Title", "latest"))
        self.assertTrue(self.helper.match_name("Any Title", "LATEST"))

    def test_match_substring(self):
        self.assertTrue(self.helper.match_name("Meeting Notes January", "meeting"))
        self.assertTrue(self.helper.match_name("Meeting Notes January", "MEETING"))
        self.assertTrue(self.helper.match_name("Meeting Notes January", "notes"))

    def test_no_match(self):
        self.assertFalse(self.helper.match_name("Meeting Notes", "interview"))


if __name__ == "__main__":
    unittest.main()
