#!/usr/bin/env python3
"""Unit tests for RiskEvaluator and related classes."""

import csv
import json
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from mode_selection import (
    MPSRiskResult,
    RiskConfig,
    RiskEvaluator,
    TranscriptionStats,
)


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


class TestRiskConfig(unittest.TestCase):
    """Tests for RiskConfig."""

    def test_default_values(self):
        config = RiskConfig()
        self.assertEqual(config.duration_safe, 1500)
        self.assertEqual(config.duration_warn, 1800)
        self.assertEqual(config.threshold_high, 30)

    def test_from_json_nonexistent(self):
        config = RiskConfig.from_json(Path("/nonexistent/config.json"))
        self.assertEqual(config.duration_safe, 1500)

    def test_from_json_valid(self):
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as f:
            json.dump({
                "duration": {"safe": 1000, "warn": 1200},
                "bitrate_high": 300,
                "thresholds": {"critical": 60, "high": 40, "moderate": 20},
            }, f)
            f.flush()

            config = RiskConfig.from_json(Path(f.name))
            self.assertEqual(config.duration_safe, 1000)
            self.assertEqual(config.duration_warn, 1200)
            self.assertEqual(config.bitrate_high, 300)
            self.assertEqual(config.threshold_critical, 60)

            Path(f.name).unlink()

    def test_to_json(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.json"
            config = RiskConfig(duration_safe=900, duration_warn=1100)
            config.to_json(config_path)

            with open(config_path) as f:
                data = json.load(f)

            self.assertEqual(data["duration"]["safe"], 900)
            self.assertEqual(data["duration"]["warn"], 1100)


class TestTranscriptionStats(unittest.TestCase):
    """Tests for TranscriptionStats."""

    def test_record_creates_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            stats_path = Path(tmpdir) / "stats.csv"
            stats = TranscriptionStats(stats_path)

            stats.record(duration=1000, bitrate=128, device="mps", success=True)

            self.assertTrue(stats_path.exists())
            with open(stats_path) as f:
                reader = csv.DictReader(f)
                rows = list(reader)
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["duration"], "1000")
            self.assertEqual(rows[0]["device"], "mps")
            self.assertEqual(rows[0]["success"], "1")

    def test_record_appends(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            stats_path = Path(tmpdir) / "stats.csv"
            stats = TranscriptionStats(stats_path)

            stats.record(duration=1000, bitrate=128, device="mps", success=True)
            stats.record(duration=2000, bitrate=128, device="mps", success=False)

            rows = stats.load()
            self.assertEqual(len(rows), 2)

    def test_analyze_empty(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            stats_path = Path(tmpdir) / "stats.csv"
            stats = TranscriptionStats(stats_path)

            analysis = stats.analyze()
            self.assertIn("error", analysis)

    def test_analyze_with_data(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            stats_path = Path(tmpdir) / "stats.csv"
            stats = TranscriptionStats(stats_path)

            stats.record(duration=1000, bitrate=128, device="mps", success=True)
            stats.record(duration=1500, bitrate=128, device="mps", success=True)
            stats.record(duration=2000, bitrate=128, device="mps", success=False)
            stats.record(duration=2500, bitrate=128, device="cpu", success=True)

            analysis = stats.analyze()

            self.assertEqual(analysis["total_records"], 4)
            self.assertEqual(analysis["mps_records"], 3)
            self.assertEqual(analysis["mps_successes"], 2)
            self.assertEqual(analysis["mps_failures"], 1)
            self.assertEqual(analysis["max_success_duration"], 1500)
            self.assertEqual(analysis["min_failure_duration"], 2000)
            self.assertIn("suggested_safe", analysis)
            self.assertIn("suggested_warn", analysis)


class TestRiskEvaluatorFailures(unittest.TestCase):
    """Tests for MPS failure tracking."""

    def test_has_recent_failure_no_log(self):
        evaluator = RiskEvaluator(failure_log_path=None)
        self.assertFalse(evaluator.has_recent_failure())

    def test_has_recent_failure_nonexistent_log(self):
        evaluator = RiskEvaluator(failure_log_path=Path("/nonexistent/file"))
        self.assertFalse(evaluator.has_recent_failure())

    def test_has_recent_failure_old_entries(self):
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".log") as f:
            old_time = int(time.time()) - 7200
            f.write(f"{old_time}\n")
            f.flush()

            evaluator = RiskEvaluator(failure_log_path=Path(f.name))
            self.assertFalse(evaluator.has_recent_failure())

            Path(f.name).unlink()

    def test_has_recent_failure_recent_entry(self):
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".log") as f:
            recent_time = int(time.time()) - 300
            f.write(f"{recent_time}\n")
            f.flush()

            evaluator = RiskEvaluator(failure_log_path=Path(f.name))
            self.assertTrue(evaluator.has_recent_failure())

            Path(f.name).unlink()

    def test_record_failure(self):
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".log") as f:
            f.close()

            evaluator = RiskEvaluator(failure_log_path=Path(f.name))
            evaluator.record_failure()

            with open(f.name) as log:
                lines = log.readlines()

            self.assertEqual(len(lines), 1)
            timestamp = int(lines[0].strip())
            self.assertAlmostEqual(timestamp, int(time.time()), delta=5)

            Path(f.name).unlink()

    def test_record_failure_keeps_last_10(self):
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".log") as f:
            for i in range(12):
                f.write(f"{int(time.time()) - i * 100}\n")
            f.flush()

            evaluator = RiskEvaluator(failure_log_path=Path(f.name))
            evaluator.record_failure()

            with open(f.name) as log:
                lines = log.readlines()

            self.assertEqual(len(lines), 10)

            Path(f.name).unlink()


class TestRiskEvaluatorEvaluate(unittest.TestCase):
    """Tests for MPS risk evaluation."""

    def setUp(self):
        self.evaluator = RiskEvaluator()

    def test_risk_low_short_duration(self):
        result = self.evaluator.evaluate(duration=600, bitrate=128)
        self.assertEqual(result.level, "low")
        self.assertEqual(result.score, 0)
        self.assertEqual(result.reasons, [])

    def test_risk_moderate_medium_duration(self):
        result = self.evaluator.evaluate(duration=1560, bitrate=128)
        self.assertEqual(result.level, "moderate")
        self.assertEqual(result.score, 20)
        self.assertIn("duration>1500s", result.reasons)

    def test_risk_high_long_duration(self):
        result = self.evaluator.evaluate(duration=2100, bitrate=128)
        self.assertEqual(result.level, "high")
        self.assertEqual(result.score, 40)
        self.assertIn("duration>1800s", result.reasons)

    def test_risk_high_bitrate_adds_score(self):
        result = self.evaluator.evaluate(duration=600, bitrate=320)
        self.assertEqual(result.score, 10)
        self.assertIn("high_bitrate:320kbps", result.reasons)

    def test_risk_recent_failure_adds_score(self):
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".log") as f:
            recent_time = int(time.time()) - 300
            f.write(f"{recent_time}\n")
            f.flush()

            evaluator = RiskEvaluator(failure_log_path=Path(f.name))
            result = evaluator.evaluate(duration=600, bitrate=128)

            self.assertEqual(result.score, 30)
            self.assertIn("recent_failure", result.reasons)

            Path(f.name).unlink()

    def test_risk_critical_multiple_factors(self):
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".log") as f:
            recent_time = int(time.time()) - 300
            f.write(f"{recent_time}\n")
            f.flush()

            evaluator = RiskEvaluator(failure_log_path=Path(f.name))
            result = evaluator.evaluate(duration=2100, bitrate=128)

            self.assertEqual(result.level, "critical")
            self.assertGreaterEqual(result.score, 50)

            Path(f.name).unlink()

    def test_risk_none_values_handled(self):
        result = self.evaluator.evaluate(duration=None, bitrate=None)
        self.assertEqual(result.level, "low")
        self.assertEqual(result.score, 0)

    def test_custom_config(self):
        config = RiskConfig(duration_safe=500, duration_warn=800)
        evaluator = RiskEvaluator(config=config)

        result = evaluator.evaluate(duration=600, bitrate=128)
        self.assertEqual(result.level, "moderate")
        self.assertIn("duration>500s", result.reasons)


class TestRiskEvaluatorGPUMemory(unittest.TestCase):
    """Tests for GPU memory detection."""

    def setUp(self):
        self.evaluator = RiskEvaluator()

    @patch("mode_selection.subprocess.run")
    def test_get_gpu_free_mb_success(self, mock_run):
        mock_run.return_value = MagicMock(
            stdout="""Mach Virtual Memory Statistics: (page size of 16384 bytes)
Pages free:                               100000.
Pages active:                             200000.
Pages inactive:                           150000.
Pages speculative:                         50000.
"""
        )
        free_mb = self.evaluator.get_gpu_free_mb()
        self.assertEqual(free_mb, 3906)

    @patch("mode_selection.subprocess.run")
    def test_get_gpu_free_mb_on_error(self, mock_run):
        mock_run.side_effect = Exception("vm_stat not found")
        free_mb = self.evaluator.get_gpu_free_mb()
        self.assertIsNone(free_mb)


if __name__ == "__main__":
    unittest.main()
