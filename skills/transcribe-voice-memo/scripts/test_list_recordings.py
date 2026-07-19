#!/usr/bin/env python3
"""Unit tests for VoiceMemoHelper class."""

import json
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from list_recordings import AudioMetadata, MPSRiskResult, VoiceMemoHelper


class TestMPSRiskResult(unittest.TestCase):
    """Tests for MPSRiskResult dataclass."""

    def test_should_use_cpu_high(self):
        result = MPSRiskResult(level="high", score=35, reasons=["duration>1800s"])
        self.assertTrue(result.should_use_cpu())

    def test_should_use_cpu_critical(self):
        result = MPSRiskResult(level="critical", score=55, reasons=["duration>1800s", "recent_failure"])
        self.assertTrue(result.should_use_cpu())

    def test_should_not_use_cpu_low(self):
        result = MPSRiskResult(level="low", score=0, reasons=[])
        self.assertFalse(result.should_use_cpu())

    def test_should_not_use_cpu_moderate(self):
        result = MPSRiskResult(level="moderate", score=20, reasons=["duration>1500s"])
        self.assertFalse(result.should_use_cpu())


class TestVoiceMemoHelperMetadata(unittest.TestCase):
    """Tests for metadata extraction methods."""

    def setUp(self):
        self.helper = VoiceMemoHelper()

    @patch("subprocess.run")
    def test_get_title_from_metadata(self, mock_run):
        mock_run.return_value = MagicMock(
            stdout='{"format": {"tags": {"title": "My Recording"}}}'
        )
        title = self.helper.get_title(Path("/fake/file.m4a"))
        self.assertEqual(title, "My Recording")

    @patch("subprocess.run")
    def test_get_title_fallback_to_filename(self, mock_run):
        mock_run.return_value = MagicMock(stdout='{"format": {}}')
        title = self.helper.get_title(Path("/fake/recording_2024.m4a"))
        self.assertEqual(title, "recording_2024")

    @patch("subprocess.run")
    def test_get_title_on_error(self, mock_run):
        mock_run.side_effect = Exception("ffprobe not found")
        title = self.helper.get_title(Path("/fake/fallback.m4a"))
        self.assertEqual(title, "fallback")

    @patch("subprocess.run")
    def test_get_duration_success(self, mock_run):
        mock_run.return_value = MagicMock(stdout="1234.56\n")
        duration = self.helper.get_duration(Path("/fake/file.m4a"))
        self.assertEqual(duration, 1234)

    @patch("subprocess.run")
    def test_get_duration_empty(self, mock_run):
        mock_run.return_value = MagicMock(stdout="")
        duration = self.helper.get_duration(Path("/fake/file.m4a"))
        self.assertIsNone(duration)

    @patch("subprocess.run")
    def test_get_duration_on_error(self, mock_run):
        mock_run.side_effect = Exception("ffprobe error")
        duration = self.helper.get_duration(Path("/fake/file.m4a"))
        self.assertIsNone(duration)

    @patch("subprocess.run")
    def test_get_bitrate_success(self, mock_run):
        mock_run.return_value = MagicMock(stdout="128000\n")
        bitrate = self.helper.get_bitrate(Path("/fake/file.m4a"))
        self.assertEqual(bitrate, 128)

    @patch("subprocess.run")
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

            # Create fake m4a files with different mtimes
            for i, name in enumerate(["old.m4a", "new.m4a", "middle.m4a"]):
                filepath = tmppath / name
                filepath.touch()
                # Set different modification times
                import os
                os.utime(filepath, (time.time() - (100 - i * 50), time.time() - (100 - i * 50)))

            helper = VoiceMemoHelper(recordings_dir=tmppath)

            with patch.object(helper, "get_title", side_effect=lambda p: p.stem):
                recordings = helper.list_recordings()

            # Should be sorted newest first
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


class TestVoiceMemoHelperMPSFailures(unittest.TestCase):
    """Tests for MPS failure tracking."""

    def test_has_recent_failure_no_log(self):
        helper = VoiceMemoHelper(failure_log_path=None)
        self.assertFalse(helper.has_recent_mps_failure())

    def test_has_recent_failure_nonexistent_log(self):
        helper = VoiceMemoHelper(failure_log_path=Path("/nonexistent/file"))
        self.assertFalse(helper.has_recent_mps_failure())

    def test_has_recent_failure_old_entries(self):
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".log") as f:
            # Write timestamp from 2 hours ago
            old_time = int(time.time()) - 7200
            f.write(f"{old_time}\n")
            f.flush()

            helper = VoiceMemoHelper(failure_log_path=Path(f.name))
            self.assertFalse(helper.has_recent_mps_failure())

            Path(f.name).unlink()

    def test_has_recent_failure_recent_entry(self):
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".log") as f:
            # Write timestamp from 5 minutes ago
            recent_time = int(time.time()) - 300
            f.write(f"{recent_time}\n")
            f.flush()

            helper = VoiceMemoHelper(failure_log_path=Path(f.name))
            self.assertTrue(helper.has_recent_mps_failure())

            Path(f.name).unlink()

    def test_record_mps_failure(self):
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".log") as f:
            f.close()  # Close so we can write to it

            helper = VoiceMemoHelper(failure_log_path=Path(f.name))
            helper.record_mps_failure()

            with open(f.name) as log:
                lines = log.readlines()

            self.assertEqual(len(lines), 1)
            timestamp = int(lines[0].strip())
            self.assertAlmostEqual(timestamp, int(time.time()), delta=5)

            Path(f.name).unlink()

    def test_record_mps_failure_keeps_last_10(self):
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".log") as f:
            # Write 12 old entries
            for i in range(12):
                f.write(f"{int(time.time()) - i * 100}\n")
            f.flush()

            helper = VoiceMemoHelper(failure_log_path=Path(f.name))
            helper.record_mps_failure()

            with open(f.name) as log:
                lines = log.readlines()

            self.assertEqual(len(lines), 10)

            Path(f.name).unlink()


class TestVoiceMemoHelperMPSRisk(unittest.TestCase):
    """Tests for MPS risk evaluation."""

    def setUp(self):
        self.helper = VoiceMemoHelper()

    def test_risk_low_short_duration(self):
        result = self.helper.evaluate_mps_risk(duration=600, bitrate=128)
        self.assertEqual(result.level, "low")
        self.assertEqual(result.score, 0)
        self.assertEqual(result.reasons, [])

    def test_risk_moderate_medium_duration(self):
        # 26 minutes - above safe threshold
        result = self.helper.evaluate_mps_risk(duration=1560, bitrate=128)
        self.assertEqual(result.level, "moderate")
        self.assertEqual(result.score, 20)
        self.assertIn("duration>1500s", result.reasons)

    def test_risk_high_long_duration(self):
        # 35 minutes - above warn threshold
        result = self.helper.evaluate_mps_risk(duration=2100, bitrate=128)
        self.assertEqual(result.level, "high")
        self.assertEqual(result.score, 40)
        self.assertIn("duration>1800s", result.reasons)

    def test_risk_high_bitrate_adds_score(self):
        result = self.helper.evaluate_mps_risk(duration=600, bitrate=320)
        self.assertEqual(result.score, 10)
        self.assertIn("high_bitrate:320kbps", result.reasons)

    def test_risk_recent_failure_adds_score(self):
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".log") as f:
            recent_time = int(time.time()) - 300
            f.write(f"{recent_time}\n")
            f.flush()

            helper = VoiceMemoHelper(failure_log_path=Path(f.name))
            result = helper.evaluate_mps_risk(duration=600, bitrate=128)

            self.assertEqual(result.score, 30)
            self.assertIn("recent_failure", result.reasons)

            Path(f.name).unlink()

    def test_risk_critical_multiple_factors(self):
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".log") as f:
            recent_time = int(time.time()) - 300
            f.write(f"{recent_time}\n")
            f.flush()

            helper = VoiceMemoHelper(failure_log_path=Path(f.name))
            # Long duration (40) + recent failure (30) = 70 = critical
            result = helper.evaluate_mps_risk(duration=2100, bitrate=128)

            self.assertEqual(result.level, "critical")
            self.assertGreaterEqual(result.score, 50)

            Path(f.name).unlink()

    def test_risk_none_values_handled(self):
        result = self.helper.evaluate_mps_risk(duration=None, bitrate=None)
        self.assertEqual(result.level, "low")
        self.assertEqual(result.score, 0)

    @patch.object(VoiceMemoHelper, "get_duration", return_value=2000)
    @patch.object(VoiceMemoHelper, "get_bitrate", return_value=256)
    def test_evaluate_mps_risk_for_file(self, mock_bitrate, mock_duration):
        result = self.helper.evaluate_mps_risk_for_file(Path("/fake/file.m4a"))
        self.assertEqual(result.level, "high")


class TestVoiceMemoHelperGPUMemory(unittest.TestCase):
    """Tests for GPU memory detection."""

    def setUp(self):
        self.helper = VoiceMemoHelper()

    @patch("subprocess.run")
    def test_get_gpu_free_mb_success(self, mock_run):
        mock_run.return_value = MagicMock(
            stdout="""Mach Virtual Memory Statistics: (page size of 16384 bytes)
Pages free:                               100000.
Pages active:                             200000.
Pages inactive:                           150000.
Pages speculative:                         50000.
"""
        )
        free_mb = self.helper.get_gpu_free_mb()
        # (100000 + 150000) * 16384 / 1024 / 1024 = 3906 MB
        self.assertEqual(free_mb, 3906)

    @patch("subprocess.run")
    def test_get_gpu_free_mb_on_error(self, mock_run):
        mock_run.side_effect = Exception("vm_stat not found")
        free_mb = self.helper.get_gpu_free_mb()
        self.assertIsNone(free_mb)


if __name__ == "__main__":
    unittest.main()
