#!/usr/bin/env python3
"""
scan_repo — orchestrator: read-only evidence scan of a repository.

Walks the repo (skipping build output, vendored code, lock files and secret
files), classifies each file into a kind, greps it with the detection signals
in config/signals.json, extracts runtime specs, and prints an evidence report.
It never writes anything and never prints a secret value (secret-looking
`key: value` lines are redacted). Classifying, inferring and drawing the
diagram are the agent's job; this script only collects the evidence.

    python3 scan_repo.py <repo> [--json] [--signals FILE] [--signals-local FILE]
                         [--max-hits N] [--bucket B ...] [--tier confident|flag]

Signals: the shipped config/signals.json, plus a local overlay merged on top
(org-specific patterns that must not be committed to the skill). The overlay is
--signals-local, else $ARCHITECTURE_REVERSE_ENGINEERING_SIGNALS_LOCAL, else
~/.config/architecture-reverse-engineering/signals.local.json if it exists.

Each hit has a tier:
  confident   a confident pattern matched: evidence for that category
  flag        a flag-only pattern matched: the agent must judge it

Buckets (from the signals file): downstream-peer, downstream-cloud, middleware,
upstream, auth, cross-cutting, inferred-clue.

Exit code: 0 = scan done (even with no hits), 1 = repo path missing or not a
directory, or the signals file is invalid. 2 = bad arguments.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter
from pathlib import Path

import arch_lib as lib

SCRIPTS_DIR = Path(__file__).resolve().parent
DEFAULT_SIGNALS = SCRIPTS_DIR.parent / "config" / "signals.json"
LOCAL_ENV = "ARCHITECTURE_REVERSE_ENGINEERING_SIGNALS_LOCAL"
DEFAULT_LOCAL = Path.home() / ".config" / "architecture-reverse-engineering" / "signals.local.json"
BUCKET_ORDER = ["upstream", "downstream-peer", "downstream-cloud", "middleware", "auth",
                "cross-cutting", "inferred-clue"]


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #

def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("repo", help="repository root to scan")
    ap.add_argument("--json", action="store_true", help="print the report as JSON (for agents)")
    ap.add_argument("--signals", default=str(DEFAULT_SIGNALS),
                    help="signals file (default: the skill's config/signals.json)")
    ap.add_argument("--signals-local", default=None,
                    help=f"local overlay merged on top (default: ${LOCAL_ENV}, "
                         f"else {DEFAULT_LOCAL} if present)")
    ap.add_argument("--no-local", action="store_true", help="ignore any local overlay")
    ap.add_argument("--max-hits", type=int, default=60,
                    help="max hits kept per category, most-cited first (default 60; 0 = no cap)")
    ap.add_argument("--bucket", action="append", default=None,
                    help="only report these buckets (repeatable)")
    ap.add_argument("--tier", choices=lib.TIERS, default=None,
                    help="only report this tier (default: both)")
    ap.add_argument("-q", "--quiet", action="store_true", help="print the summary only")
    return ap.parse_args(argv)


def resolve_local(args: argparse.Namespace) -> Path | None:
    """Pick the local overlay path: flag, env var, default file, or none."""
    if args.no_local:
        return None
    if args.signals_local:
        return Path(args.signals_local).expanduser()
    env = os.environ.get(LOCAL_ENV)
    if env:
        return Path(env).expanduser()
    return DEFAULT_LOCAL if DEFAULT_LOCAL.is_file() else None


# --------------------------------------------------------------------------- #
# Scan
# --------------------------------------------------------------------------- #

def scan(root: Path, compiled: lib.Compiled) -> dict:
    """Walk the repo once; return inventory, hits, specs and counters."""
    inventory, hits, specs = [], [], []
    kinds: Counter = Counter()
    skipped = {"binary": 0, "too-large": 0, "unknown-kind": 0, "unreadable": 0}
    for rel, full in lib.iter_repo_files(root, compiled):
        kind = lib.file_kind(rel, compiled)
        reveals = lib.inventory_reveals(rel, compiled)
        if reveals:
            inventory.append({"path": rel, "kind": kind, "reveals": reveals})
        if kind is None:
            skipped["unknown-kind"] += 1
            continue
        try:
            if full.stat().st_size > compiled.max_file_bytes:
                skipped["too-large"] += 1
                continue
            if lib.is_binary(full):
                skipped["binary"] += 1
                continue
            text = lib.read_text(full)
        except OSError as exc:
            print(f"scan_repo: cannot read {rel}: {exc}", file=sys.stderr)
            skipped["unreadable"] += 1
            continue
        kinds[kind] += 1
        hits.extend(lib.scan_text(text, rel, kind, compiled))
        specs.extend(lib.extract_specs(text, rel, compiled))
    return {"inventory": inventory, "hits": hits, "specs": specs,
            "kinds": dict(kinds), "skipped": skipped}


def select(hits: list[lib.Hit], buckets: list[str] | None, tier: str | None,
           max_hits: int) -> tuple[list[lib.Hit], dict[str, int]]:
    """Filter hits and cap each category; return kept hits + dropped count per category."""
    kept, dropped = [], {}
    by_cat: dict[str, list[lib.Hit]] = {}
    for h in hits:
        if buckets and h.bucket not in buckets:
            continue
        if tier and h.tier != tier:
            continue
        by_cat.setdefault(h.category, []).append(h)
    for cat, items in by_cat.items():
        items.sort(key=lambda h: (h.tier != "confident", -len(h.lines), h.path, h.match.lower()))
        if max_hits and len(items) > max_hits:
            dropped[cat] = len(items) - max_hits
            items = items[:max_hits]
        kept.extend(items)
    order = {b: i for i, b in enumerate(BUCKET_ORDER)}
    kept.sort(key=lambda h: (order.get(h.bucket, 99), h.category, h.tier != "confident",
                             h.path, h.lines[0]))
    return kept, dropped


# --------------------------------------------------------------------------- #
# Report
# --------------------------------------------------------------------------- #

def build_report(root: Path, result: dict, hits: list[lib.Hit], dropped: dict[str, int],
                 signals_used: list[str]) -> dict:
    by_bucket = Counter(h.bucket for h in hits)
    by_tier = Counter(h.tier for h in hits)
    return {
        "repo": str(root),
        "signals": signals_used,
        "summary": {
            "files_scanned": sum(result["kinds"].values()),
            "files_by_kind": result["kinds"],
            "files_skipped": result["skipped"],
            "hits": len(hits),
            "hits_by_tier": {t: by_tier.get(t, 0) for t in lib.TIERS},
            "hits_by_bucket": dict(sorted(by_bucket.items(),
                                          key=lambda kv: BUCKET_ORDER.index(kv[0])
                                          if kv[0] in BUCKET_ORDER else 99)),
            "truncated": dropped,
        },
        "inventory": result["inventory"],
        "runtime_specs": [vars(s) for s in result["specs"]],
        "hits": [vars(h) for h in hits],
    }


def print_text(report: dict, quiet: bool) -> None:
    s = report["summary"]
    print(f"repo: {report['repo']}")
    print(f"files scanned: {s['files_scanned']}  hits: {s['hits']} "
          f"(confident {s['hits_by_tier']['confident']}, flag {s['hits_by_tier']['flag']})")
    if s["truncated"]:
        print("truncated: " + ", ".join(f"{c} +{n}" for c, n in s["truncated"].items())
              + "  (raise --max-hits to see all)")
    if quiet:
        return
    print("\n[inventory]")
    for item in report["inventory"]:
        print(f"  {item['path']}  — {item['reveals']}")
    print("\n[runtime-specs]")
    for spec in report["runtime_specs"]:
        print(f"  {spec['spec']}: {spec['value']}  ({spec['path']}:{spec['line']})")
    bucket = None
    for h in report["hits"]:
        if h["bucket"] != bucket:
            bucket = h["bucket"]
            print(f"\n[{bucket}]")
        lines = ",".join(str(n) for n in h["lines"][:8]) + ("…" if len(h["lines"]) > 8 else "")
        mark = "" if h["tier"] == "confident" else " ?"
        print(f"  {h['category']}{mark}  {h['match']}  {h['path']}:{lines}  | {h['snippet']}")


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    root = Path(args.repo).expanduser()
    if not root.is_dir():
        print(f"scan_repo: not a directory: {root}", file=sys.stderr)
        return 1
    try:
        signals = lib.load_signals(args.signals)
        used = [str(Path(args.signals).resolve())]
        local = resolve_local(args)
        if local is not None:
            if not local.is_file():
                raise lib.SignalsError(f"local signals overlay not found: {local}")
            overlay = json.loads(local.read_text(encoding="utf-8"))
            signals = lib.merge_signals(signals, overlay)
            used.append(str(local.resolve()))
        compiled = lib.compile_signals(signals)
    except (lib.SignalsError, json.JSONDecodeError) as exc:
        print(f"scan_repo: {exc}", file=sys.stderr)
        return 1
    print(f"scan_repo: scanning {root.resolve()}", file=sys.stderr)
    result = scan(root, compiled)
    hits, dropped = select(result["hits"], args.bucket, args.tier, args.max_hits)
    report = build_report(root.resolve(), result, hits, dropped, used)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print_text(report, args.quiet)
    return 0


if __name__ == "__main__":
    sys.exit(main())
