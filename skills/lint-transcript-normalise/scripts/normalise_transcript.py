#!/usr/bin/env python3
"""
Normalise proper nouns in an auto-generated transcript (Whisper/Zoom/xxx).

Driven by a JSON correction dictionary (config/corrections.json) that maps each
canonical entity to:
  - variants:            genuine garbles -> auto-fixed to the correct PLAIN-TEXT name
  - ambiguous_variants:  risky tokens    -> only FLAGGED with file:line, never replaced

Two-phase design so a wrong name never gets silently written:
  1. Confident pass  -> rewrite distinctive mis-spellings to the correct plain name.
  2. Ambiguous pass  -> emit an "Entities to confirm" report for human review.

This tool fixes spelling only; it does NOT inject [[wikilinks]] into the source
(that stays the ingest step's job). The report surfaces the wikilink target so the
reviewer / ingest can link confirmed mentions.

Usage:
    normalise_transcript.py TRANSCRIPT [--corrections FILE] [--write]

    (default is a dry run; nothing is written without --write)

Matching rules:
  - Confident variants: case-INsensitive, whole-word, and never applied inside an
    existing [[wikilink]] span (those are masked out first).
  - Ambiguous variants: case-SENSITIVE, whole-word (keeps single letters like "G"
    from matching every stray lowercase "g").

Stdlib only. Exit code 0 always (report tool, not a gate).
"""

import argparse
import json
import re
import sys
from pathlib import Path


WIKILINK_SPAN = re.compile(r"\[\[.*?\]\]")


def load_corrections(path: Path) -> dict:
    with path.open(encoding="utf-8") as fh:
        return json.load(fh)


def word_pattern(token: str, ignore_case: bool) -> re.Pattern:
    flags = re.IGNORECASE if ignore_case else 0
    return re.compile(rf"(?<![\w-])({re.escape(token)})(?![\w-])", flags)


def replace_confident(content: str, corrections: list) -> tuple[str, list]:
    """Fix confident garbles to the correct plain-text name, skipping [[...]] spans."""
    # Split into (text, link, text, link, ...) so we never touch link spans.
    parts = WIKILINK_SPAN.split(content)
    links = WIKILINK_SPAN.findall(content)

    changes = []  # (correct, variant, count)
    for entry in corrections:
        correct = entry.get("correct")
        if not correct:
            continue
        for variant in entry.get("variants", []):
            pat = word_pattern(variant, ignore_case=True)
            total = 0
            for i, seg in enumerate(parts):
                new_seg, n = pat.subn(correct, seg)
                if n:
                    parts[i] = new_seg
                    total += n
            if total:
                changes.append((entry["correct"], variant, total))

    # Reassemble text + preserved links.
    out = []
    for i, seg in enumerate(parts):
        out.append(seg)
        if i < len(links):
            out.append(links[i])
    return "".join(out), changes


def scan_ambiguous(content: str, corrections: list) -> list:
    """Find ambiguous variants line-by-line for a confirmation report."""
    lines = content.splitlines()
    hits = []  # (correct, wikilink, variant, lineno, line_text)
    for entry in corrections:
        for variant in entry.get("ambiguous_variants", []):
            pat = word_pattern(variant, ignore_case=False)
            for lineno, line in enumerate(lines, start=1):
                if pat.search(line):
                    hits.append(
                        (
                            entry["correct"],
                            entry.get("wikilink", ""),
                            variant,
                            lineno,
                            line.strip(),
                        )
                    )
    return hits


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("transcript", type=Path, help="Path to the transcript markdown file")
    default_cfg = Path(__file__).resolve().parent.parent / "config" / "corrections.json"
    ap.add_argument("--corrections", type=Path, default=default_cfg, help=f"Correction dictionary (default: {default_cfg})")
    ap.add_argument("--write", action="store_true", help="Apply confident replacements in place (default: dry run)")
    args = ap.parse_args()

    if not args.transcript.exists():
        print(f"error: transcript not found: {args.transcript}", file=sys.stderr)
        return 2
    if not args.corrections.exists():
        print(f"error: corrections file not found: {args.corrections}", file=sys.stderr)
        return 2

    cfg = load_corrections(args.corrections)
    corrections = cfg.get("corrections", [])
    original = args.transcript.read_text(encoding="utf-8")

    new_content, changes = replace_confident(original, corrections)
    ambiguous = scan_ambiguous(new_content, corrections)

    mode = "WRITE" if args.write else "DRY-RUN"
    print(f"# transcript-normalise [{mode}] {args.transcript}")
    print(f"# dictionary: {args.corrections} (v{cfg.get('version', '?')}, {len(corrections)} entities)\n")

    print("## Confident replacements (auto-applied)" if args.write else "## Confident replacements (would apply)")
    if changes:
        for correct, variant, count in changes:
            print(f"  {count:>3}x  {variant!r} -> {correct}")
    else:
        print("  (none)")

    print("\n## Entities to confirm (NEVER auto-replaced — decide per line)")
    if ambiguous:
        for correct, wikilink, variant, lineno, text in ambiguous:
            print(f"  L{lineno}: {variant!r} -> maybe {correct} {wikilink}".rstrip())
            print(f"        | {text}")
    else:
        print("  (none)")

    if args.write:
        if new_content != original:
            args.transcript.write_text(new_content, encoding="utf-8")
            print(f"\nWrote {args.transcript}")
        else:
            print("\nNo confident changes; file unchanged.")
    else:
        print("\n(dry run — re-run with --write to apply confident replacements)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
