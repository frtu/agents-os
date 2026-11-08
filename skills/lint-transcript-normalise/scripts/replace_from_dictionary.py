#!/usr/bin/env python3
"""
Apply the correction dictionary to text files directly, with no LLM in the loop.

The dictionary (config/corrections.json) is used as-is: every confident `variants`
entry is replaced by its `correct` spelling. Nothing is learned: the dictionary
does not grow, ambiguous tokens are never resolved, unlisted garbles stay as they
are. Growing the dictionary is the optional "intelligence" layer of the
lint-transcript-normalise skill (manual sweep + user confirmation + write-back).

Matching rules are owned by normalise_transcript.py and imported from it:
  - `variants`: case-insensitive, whole-word, never inside an existing [[wikilink]].
  - `ambiguous_variants`: NEVER replaced; only counted (`--list-ambiguous` prints them).

Usage:
    replace_from_dictionary.py PATH [PATH ...] [--corrections FILE]
                               [--write | --out-dir DIR] [--list-ambiguous]
    replace_from_dictionary.py - < in.md > out.md      # stdin -> stdout filter

    PATH is a file or a directory (all *.md files below it, recursively).
    Default is a dry run: report what would change, write nothing.
    --write    rewrite files in place (refused inside raw/: source material is immutable)
    --out-dir  write corrected copies under DIR, mirroring each input's relative path
               (allowed for raw/ inputs, as the source stays untouched)

Stdlib only. Exit 0 on success (whether or not anything changed), 2 on usage errors.
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from normalise_transcript import load_corrections, replace_confident, scan_ambiguous  # noqa: E402

DEFAULT_CFG = Path(__file__).resolve().parent.parent / "config" / "corrections.json"


def collect(paths: list[Path]) -> list[tuple[Path, Path]]:
    """Return (file, path relative to its input root) pairs, sorted, deduplicated."""
    seen, out = set(), []
    for p in paths:
        if p.is_dir():
            items = [(f, f.relative_to(p)) for f in sorted(p.rglob("*.md")) if f.is_file()]
        else:
            items = [(p, Path(p.name))]
        for f, rel in items:
            key = f.resolve()
            if key not in seen:
                seen.add(key)
                out.append((f, rel))
    return out


def in_raw(path: Path) -> bool:
    return "raw" in path.resolve().parts


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("paths", nargs="+", help="Files or directories (*.md), or '-' for stdin -> stdout")
    ap.add_argument("--corrections", type=Path, default=DEFAULT_CFG, help=f"Dictionary (default: {DEFAULT_CFG})")
    mode = ap.add_mutually_exclusive_group()
    mode.add_argument("--write", action="store_true", help="Rewrite files in place")
    mode.add_argument("--out-dir", type=Path, help="Write corrected copies under this directory")
    ap.add_argument("--list-ambiguous", action="store_true", help="Print each ambiguous hit (file:line)")
    args = ap.parse_args(argv)

    if not args.corrections.exists():
        print(f"error: corrections file not found: {args.corrections}", file=sys.stderr)
        return 2
    cfg = load_corrections(args.corrections)
    corrections = cfg.get("corrections", [])

    # Filter mode: stdin -> stdout, report on stderr.
    if args.paths == ["-"]:
        if args.write or args.out_dir:
            print("error: '-' (stdin) cannot be combined with --write or --out-dir", file=sys.stderr)
            return 2
        new, changes = replace_confident(sys.stdin.read(), corrections)
        sys.stdout.write(new)
        total = sum(c for _, _, c in changes)
        amb = len(scan_ambiguous(new, corrections))
        print(f"replace-from-dictionary: {total} replacement(s), {amb} ambiguous left", file=sys.stderr)
        return 0

    paths = [Path(p) for p in args.paths]
    missing = [p for p in paths if not p.exists()]
    if missing:
        print("error: not found: " + ", ".join(map(str, missing)), file=sys.stderr)
        return 2
    files = collect(paths)
    if args.write:
        blocked = [f for f, _ in files if in_raw(f)]
        if blocked:
            print(
                "error: refusing --write inside raw/ (immutable source material):\n  "
                + "\n  ".join(map(str, blocked))
                + "\n  Use --out-dir to write corrected copies elsewhere.",
                file=sys.stderr,
            )
            return 2

    label = "WRITE" if args.write else (f"OUT-DIR {args.out_dir}" if args.out_dir else "DRY-RUN")
    print(f"# replace-from-dictionary [{label}]")
    print(f"# dictionary: {args.corrections} (v{cfg.get('version', '?')}, {len(corrections)} entities)\n")

    grand_total = grand_amb = changed_files = 0
    for f, rel in files:
        original = f.read_text(encoding="utf-8")
        new, changes = replace_confident(original, corrections)
        ambiguous = scan_ambiguous(new, corrections)
        total = sum(c for _, _, c in changes)
        grand_total += total
        grand_amb += len(ambiguous)
        changed_files += bool(total)

        if total or ambiguous:
            print(f"{f}: {total} replacement(s), {len(ambiguous)} ambiguous")
            for correct, variant, count in changes:
                print(f"  {count:>3}x  {variant!r} -> {correct}")
            if args.list_ambiguous:
                for correct, _link, variant, lineno, _text in ambiguous:
                    print(f"  L{lineno}: {variant!r} (maybe {correct}) — left as is")

        if args.write and new != original:
            f.write_text(new, encoding="utf-8")
        elif args.out_dir:
            dest = args.out_dir / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(new, encoding="utf-8")

    print(f"\n{len(files)} file(s), {changed_files} changed, {grand_total} replacement(s), {grand_amb} ambiguous left")
    if not args.write and not args.out_dir:
        print("(dry run: re-run with --write or --out-dir DIR to apply)")
    if grand_amb:
        print("(ambiguous tokens are never replaced; resolve them with the skill to grow the dictionary)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
