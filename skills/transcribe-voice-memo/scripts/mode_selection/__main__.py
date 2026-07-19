#!/usr/bin/env python3
"""CLI entry point for mode_selection module."""

import argparse
import sys
from pathlib import Path

from . import (
    DEFAULT_CONFIG_PATH,
    MPSRiskResult,
    RiskConfig,
    RiskEvaluator,
    TranscriptionStats,
)


def main():
    parser = argparse.ArgumentParser(description="MPS Risk Evaluator")
    subparsers = parser.add_subparsers(dest="command", required=True, help="Command to run")

    # evaluate command
    eval_parser = subparsers.add_parser("evaluate", help="Evaluate MPS risk")
    eval_parser.add_argument("--duration", type=int, default=None, help="Audio duration in seconds")
    eval_parser.add_argument("--bitrate", type=int, default=None, help="Audio bitrate in kbps")
    eval_parser.add_argument("--failure-log", type=str, default=None, help="Path to MPS failure log")
    eval_parser.add_argument("--config", type=str, default=None, help="Path to config JSON")
    eval_parser.add_argument("--duration-safe", type=int, default=None, help="Override safe duration threshold")
    eval_parser.add_argument("--duration-warn", type=int, default=None, help="Override warn duration threshold")

    # record-failure command
    fail_parser = subparsers.add_parser("record-failure", help="Record an MPS failure")
    fail_parser.add_argument("--failure-log", type=str, required=True, help="Path to MPS failure log")

    # record-result command
    result_parser = subparsers.add_parser("record-result", help="Record transcription result")
    result_parser.add_argument("--duration", type=int, default=None, help="Audio duration")
    result_parser.add_argument("--bitrate", type=int, default=None, help="Audio bitrate")
    result_parser.add_argument("--device", type=str, required=True, help="Device used (mps/cpu)")
    result_parser.add_argument("--success", action="store_true", help="Transcription succeeded")
    result_parser.add_argument("--failure", action="store_true", help="Transcription failed")
    result_parser.add_argument("--risk-level", type=str, default="", help="Risk level at evaluation")
    result_parser.add_argument("--risk-score", type=int, default=0, help="Risk score at evaluation")
    result_parser.add_argument("--stats-path", type=str, default=None, help="Path to stats CSV")

    # analyze command
    analyze_parser = subparsers.add_parser("analyze", help="Analyze statistics")
    analyze_parser.add_argument("--stats-path", type=str, default=None, help="Path to stats CSV")

    # calibrate command
    calibrate_parser = subparsers.add_parser("calibrate", help="Update config from statistics")
    calibrate_parser.add_argument("--stats-path", type=str, default=None, help="Path to stats CSV")
    calibrate_parser.add_argument("--config", type=str, default=None, help="Path to config JSON")
    calibrate_parser.add_argument("--dry-run", action="store_true", help="Show changes without applying")

    # show-config command
    config_parser = subparsers.add_parser("show-config", help="Show current configuration")
    config_parser.add_argument("--config", type=str, default=None, help="Path to config JSON")

    args = parser.parse_args()

    if args.command == "evaluate":
        config_path = Path(args.config) if args.config else DEFAULT_CONFIG_PATH
        config = RiskConfig.from_json(config_path)

        if args.duration_safe is not None:
            config.duration_safe = args.duration_safe
        if args.duration_warn is not None:
            config.duration_warn = args.duration_warn

        failure_log = Path(args.failure_log) if args.failure_log else None
        evaluator = RiskEvaluator(failure_log_path=failure_log, config=config)
        risk = evaluator.evaluate(args.duration, args.bitrate)

        print(f"level:{risk.level}")
        print(f"score:{risk.score}")
        print(f"use_cpu:{1 if risk.should_use_cpu() else 0}")
        print(f"reasons:{','.join(risk.reasons) if risk.reasons else 'none'}")

    elif args.command == "record-failure":
        failure_log = Path(args.failure_log)
        evaluator = RiskEvaluator(failure_log_path=failure_log)
        evaluator.record_failure()
        print("Recorded MPS failure")

    elif args.command == "record-result":
        if not args.success and not args.failure:
            print("Error: Must specify --success or --failure", file=sys.stderr)
            sys.exit(1)

        stats_path = Path(args.stats_path) if args.stats_path else None
        stats = TranscriptionStats(stats_path)
        stats.record(
            duration=args.duration,
            bitrate=args.bitrate,
            device=args.device,
            success=args.success,
            risk_level=args.risk_level,
            risk_score=args.risk_score,
        )
        print(f"Recorded {'success' if args.success else 'failure'} for {args.device}")

    elif args.command == "analyze":
        stats_path = Path(args.stats_path) if args.stats_path else None
        stats = TranscriptionStats(stats_path)
        analysis = stats.analyze()

        if "error" in analysis:
            print(f"Error: {analysis['error']}", file=sys.stderr)
            sys.exit(1)

        print(f"total_records:{analysis['total_records']}")
        print(f"mps_records:{analysis['mps_records']}")
        print(f"mps_successes:{analysis['mps_successes']}")
        print(f"mps_failures:{analysis['mps_failures']}")
        if "max_success_duration" in analysis:
            print(f"max_success_duration:{analysis['max_success_duration']}")
        if "min_failure_duration" in analysis:
            print(f"min_failure_duration:{analysis['min_failure_duration']}")
        if "suggested_safe" in analysis:
            print(f"suggested_safe:{analysis['suggested_safe']}")
        if "suggested_warn" in analysis:
            print(f"suggested_warn:{analysis['suggested_warn']}")

    elif args.command == "calibrate":
        stats_path = Path(args.stats_path) if args.stats_path else None
        config_path = Path(args.config) if args.config else DEFAULT_CONFIG_PATH

        stats = TranscriptionStats(stats_path)
        analysis = stats.analyze()

        if "error" in analysis:
            print(f"Error: {analysis['error']}", file=sys.stderr)
            sys.exit(1)

        if "suggested_safe" not in analysis:
            print("Error: Not enough data to calibrate", file=sys.stderr)
            sys.exit(1)

        config = RiskConfig.from_json(config_path)
        old_safe = config.duration_safe
        old_warn = config.duration_warn

        config.duration_safe = analysis["suggested_safe"]
        config.duration_warn = analysis["suggested_warn"]

        print(f"duration_safe: {old_safe} -> {config.duration_safe}")
        print(f"duration_warn: {old_warn} -> {config.duration_warn}")

        if not args.dry_run:
            config.to_json(config_path)
            print(f"Config updated: {config_path}")
        else:
            print("(dry-run, no changes saved)")

    elif args.command == "show-config":
        config_path = Path(args.config) if args.config else DEFAULT_CONFIG_PATH
        config = RiskConfig.from_json(config_path)

        print(f"config_path:{config_path}")
        print(f"duration_safe:{config.duration_safe}")
        print(f"duration_warn:{config.duration_warn}")
        print(f"bitrate_high:{config.bitrate_high}")
        print(f"gpu_min_free_mb:{config.gpu_min_free_mb}")
        print(f"threshold_critical:{config.threshold_critical}")
        print(f"threshold_high:{config.threshold_high}")


if __name__ == "__main__":
    main()
