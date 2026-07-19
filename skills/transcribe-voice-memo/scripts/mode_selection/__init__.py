"""MPS risk evaluation for Whisper transcription device selection."""

import csv
import json
import subprocess
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

DEFAULT_CONFIG_PATH = Path(__file__).parent.parent.parent / "config" / "risk_thresholds.json"
DEFAULT_STATS_PATH = Path(__file__).parent.parent.parent / "config" / "transcription_stats.csv"


@dataclass
class RiskConfig:
    """Configuration for risk evaluation thresholds."""
    duration_safe: int = 1500
    duration_warn: int = 1800
    bitrate_high: int = 256
    gpu_min_free_mb: int = 2048
    failure_window_seconds: int = 3600
    score_duration_high: int = 40
    score_duration_moderate: int = 20
    score_recent_failure: int = 30
    score_low_memory: int = 25
    score_high_bitrate: int = 10
    threshold_critical: int = 50
    threshold_high: int = 30
    threshold_moderate: int = 15

    @classmethod
    def from_json(cls, path: Path) -> "RiskConfig":
        """Load config from JSON file."""
        if not path.exists():
            return cls()
        try:
            with open(path) as f:
                data = json.load(f)
            return cls(
                duration_safe=data.get("duration", {}).get("safe", 1500),
                duration_warn=data.get("duration", {}).get("warn", 1800),
                bitrate_high=data.get("bitrate_high", 256),
                gpu_min_free_mb=data.get("gpu_min_free_mb", 2048),
                failure_window_seconds=data.get("failure_window_seconds", 3600),
                score_duration_high=data.get("scores", {}).get("duration_high", 40),
                score_duration_moderate=data.get("scores", {}).get("duration_moderate", 20),
                score_recent_failure=data.get("scores", {}).get("recent_failure", 30),
                score_low_memory=data.get("scores", {}).get("low_memory", 25),
                score_high_bitrate=data.get("scores", {}).get("high_bitrate", 10),
                threshold_critical=data.get("thresholds", {}).get("critical", 50),
                threshold_high=data.get("thresholds", {}).get("high", 30),
                threshold_moderate=data.get("thresholds", {}).get("moderate", 15),
            )
        except Exception:
            return cls()

    def to_json(self, path: Path) -> None:
        """Save config to JSON file."""
        data = {
            "duration": {
                "safe": self.duration_safe,
                "warn": self.duration_warn,
            },
            "bitrate_high": self.bitrate_high,
            "gpu_min_free_mb": self.gpu_min_free_mb,
            "failure_window_seconds": self.failure_window_seconds,
            "scores": {
                "duration_high": self.score_duration_high,
                "duration_moderate": self.score_duration_moderate,
                "recent_failure": self.score_recent_failure,
                "low_memory": self.score_low_memory,
                "high_bitrate": self.score_high_bitrate,
            },
            "thresholds": {
                "critical": self.threshold_critical,
                "high": self.threshold_high,
                "moderate": self.threshold_moderate,
            },
        }
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            json.dump(data, f, indent=2)


@dataclass
class MPSRiskResult:
    """Result of MPS failure risk evaluation."""
    level: str  # low, moderate, high, critical
    score: int
    reasons: list[str]

    def should_use_cpu(self) -> bool:
        return self.level in ("high", "critical")


class TranscriptionStats:
    """Track transcription outcomes for calibration."""

    FIELDS = [
        "timestamp", "duration", "bitrate", "device", "success", "risk_level", "risk_score",
        "file_size_bytes", "sample_rate_hz", "channels", "codec",
    ]

    def __init__(self, stats_path: Optional[Path] = None):
        self.stats_path = stats_path or DEFAULT_STATS_PATH

    def record(
        self,
        duration: Optional[int],
        bitrate: Optional[int],
        device: str,
        success: bool,
        risk_level: str = "",
        risk_score: int = 0,
        file_size_bytes: Optional[int] = None,
        sample_rate_hz: Optional[int] = None,
        channels: Optional[int] = None,
        codec: Optional[str] = None,
    ) -> None:
        """Record a transcription outcome."""
        self.stats_path.parent.mkdir(parents=True, exist_ok=True)
        file_exists = self.stats_path.exists()

        with open(self.stats_path, "a", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=self.FIELDS)
            if not file_exists:
                writer.writeheader()
            writer.writerow({
                "timestamp": datetime.now().isoformat(),
                "duration": duration or "",
                "bitrate": bitrate or "",
                "device": device,
                "success": "1" if success else "0",
                "risk_level": risk_level,
                "risk_score": risk_score,
                "file_size_bytes": file_size_bytes or "",
                "sample_rate_hz": sample_rate_hz or "",
                "channels": channels or "",
                "codec": codec or "",
            })

    def load(self) -> list[dict]:
        """Load all statistics."""
        if not self.stats_path.exists():
            return []
        with open(self.stats_path, newline="") as f:
            return list(csv.DictReader(f))

    def analyze(self) -> dict:
        """Analyze statistics and suggest threshold updates."""
        records = self.load()
        if not records:
            return {"error": "No statistics available"}

        mps_records = [r for r in records if r["device"] == "mps" and r["duration"]]
        if not mps_records:
            return {"error": "No MPS transcription records with duration"}

        successes = [int(r["duration"]) for r in mps_records if r["success"] == "1"]
        failures = [int(r["duration"]) for r in mps_records if r["success"] == "0"]

        result = {
            "total_records": len(records),
            "mps_records": len(mps_records),
            "mps_successes": len(successes),
            "mps_failures": len(failures),
        }

        if successes:
            result["max_success_duration"] = max(successes)
            result["avg_success_duration"] = sum(successes) // len(successes)

        if failures:
            result["min_failure_duration"] = min(failures)
            result["avg_failure_duration"] = sum(failures) // len(failures)

        if successes and failures:
            max_success = max(successes)
            min_failure = min(failures)
            if max_success < min_failure:
                result["suggested_safe"] = max_success
                result["suggested_warn"] = (max_success + min_failure) // 2
            else:
                result["suggested_safe"] = min(max_success, min_failure) - 60
                result["suggested_warn"] = min_failure - 30
        elif successes:
            result["suggested_safe"] = int(max(successes) * 0.9)
            result["suggested_warn"] = max(successes)
        elif failures:
            result["suggested_safe"] = int(min(failures) * 0.7)
            result["suggested_warn"] = int(min(failures) * 0.85)

        return result


class RiskEvaluator:
    """Evaluates MPS failure risk for Whisper transcription."""

    def __init__(
        self,
        failure_log_path: Optional[Path] = None,
        config: Optional[RiskConfig] = None,
        config_path: Optional[Path] = None,
    ):
        self.failure_log_path = failure_log_path
        if config:
            self.config = config
        elif config_path:
            self.config = RiskConfig.from_json(config_path)
        else:
            self.config = RiskConfig.from_json(DEFAULT_CONFIG_PATH)

    def has_recent_failure(self) -> bool:
        """Check if MPS failed recently (within failure window)."""
        if not self.failure_log_path or not self.failure_log_path.exists():
            return False

        now = int(time.time())
        cutoff = now - self.config.failure_window_seconds

        try:
            with open(self.failure_log_path) as f:
                for line in f:
                    line = line.strip()
                    if line and int(line) > cutoff:
                        return True
        except Exception:
            pass
        return False

    def record_failure(self) -> None:
        """Record an MPS failure timestamp."""
        if not self.failure_log_path:
            return

        try:
            timestamps = []
            if self.failure_log_path.exists():
                with open(self.failure_log_path) as f:
                    timestamps = [line.strip() for line in f if line.strip()]

            timestamps.append(str(int(time.time())))
            timestamps = timestamps[-10:]

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
                return (free_pages + inactive_pages) * 16384 // 1024 // 1024
        except Exception:
            pass
        return None

    def evaluate(
        self,
        duration: Optional[int] = None,
        bitrate: Optional[int] = None,
    ) -> MPSRiskResult:
        """Evaluate MPS failure risk based on multiple factors."""
        score = 0
        reasons = []
        cfg = self.config

        if duration is not None:
            if duration > cfg.duration_warn:
                score += cfg.score_duration_high
                reasons.append(f"duration>{cfg.duration_warn}s")
            elif duration > cfg.duration_safe:
                score += cfg.score_duration_moderate
                reasons.append(f"duration>{cfg.duration_safe}s")

        if self.has_recent_failure():
            score += cfg.score_recent_failure
            reasons.append("recent_failure")

        gpu_free = self.get_gpu_free_mb()
        if gpu_free is not None and gpu_free < cfg.gpu_min_free_mb:
            score += cfg.score_low_memory
            reasons.append(f"low_memory:{gpu_free}MB")

        if bitrate is not None and bitrate > cfg.bitrate_high:
            score += cfg.score_high_bitrate
            reasons.append(f"high_bitrate:{bitrate}kbps")

        if score >= cfg.threshold_critical:
            level = "critical"
        elif score >= cfg.threshold_high:
            level = "high"
        elif score >= cfg.threshold_moderate:
            level = "moderate"
        else:
            level = "low"

        return MPSRiskResult(level=level, score=score, reasons=reasons)
