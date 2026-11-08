#!/usr/bin/env python3
"""
Replace verbose phrases with direct words, driven by config/word-replacements.json.
No LLM needed: the dictionary is applied as-is.

Tiers (see the JSON's "rules"):
  - replacements: AUTO, applied on --write.
  - suggestions:  REVIEW, never applied; reported with line numbers.

Matching: case-insensitive, whole-word, any whitespace (incl. a line break) between
words; the replacement keeps the match's capitalisation ("In order to" -> "To",
"IN ORDER TO" -> "TO"). One pass per tier with the longest phrase first, so a
replacement never feeds another. Never inside fenced code blocks, inline code,
[[wikilinks]], markdown link targets "(...)" or bare URLs.

Usage:
    replace_words.py PATH [PATH ...] [--config FILE] [--write]
    replace_words.py - < in.md > out.md        # stdin -> stdout filter

    PATH is a file or a directory (all *.md below it, recursively).
    Default is a dry run: per-line report, nothing written.

Stdlib only. Exit 0 on success (whether or not anything matched), 2 on usage errors.
"""

import argparse
import json
import re
import sys
from pathlib import Path

DEFAULT_CFG = Path(__file__).resolve().parent.parent / "config" / "word-replacements.json"

# Spans never touched: fenced code, inline code, wikilinks, link targets, bare URLs.
PROTECTED = re.compile(
    r"```.*?```|~~~.*?~~~|`[^`\n]+`|\[\[.*?\]\]|\]\([^)\s]*\)|https?://\S+",
    re.DOTALL,
)


def load(path: Path) -> dict:
    with path.open(encoding="utf-8") as fh:
        return json.load(fh)


def normalise(phrase: str) -> str:
    return " ".join(phrase.lower().split())


def match_case(src: str, repl: str) -> str:
    if src.isupper() and len(src) > 1:
        return repl.upper()
    if src[:1].isupper():
        return repl[:1].upper() + repl[1:]
    return repl


def compile_tier(entries: list) -> tuple:
    """One alternation per tier, longest phrase first. Returns (pattern or None, lookup)."""
    valid = [e for e in entries if e.get("verbose") and e.get("direct") is not None]
    if not valid:
        return None, {}
    valid.sort(key=lambda e: len(e["verbose"]), reverse=True)
    body = "|".join(r"\s+".join(re.escape(w) for w in e["verbose"].split()) for e in valid)
    pattern = re.compile(r"(?<![\w-])(?:" + body + r")(?![\w-])", re.IGNORECASE)
    return pattern, {normalise(e["verbose"]): e["direct"] for e in valid}


def apply(content: str, cfg: dict) -> tuple:
    """Return (new_content, applied, suggested); lists of (line, found, direct), input line numbers."""
    auto_pat, auto_map = compile_tier(cfg.get("replacements", []))
    sugg_pat, sugg_map = compile_tier(cfg.get("suggestions", []))
    applied, suggested, out = [], [], []
    pos = 0
    for m in list(PROTECTED.finditer(content)) + [None]:
        end = m.start() if m else len(content)
        seg = content[pos:end]
        line0 = content.count("\n", 0, pos) + 1

        def line(h, seg=seg, line0=line0):
            return line0 + seg.count("\n", 0, h.start())

        if sugg_pat:
            for h in sugg_pat.finditer(seg):
                suggested.append((line(h), h.group(0), match_case(h.group(0), sugg_map[normalise(h.group(0))])))
        if auto_pat:
            def sub(h):
                new = match_case(h.group(0), auto_map[normalise(h.group(0))])
                applied.append((line(h), h.group(0), new))
                return new

            seg = auto_pat.sub(sub, seg)
        out.append(seg)
        if m:
            out.append(m.group(0))
            pos = m.end()
    return "".join(out), applied, suggested


def collect(paths: list) -> list:
    seen, out = set(), []
    for p in paths:
        for f in (sorted(p.rglob("*.md")) if p.is_dir() else [p]):
            if f.is_file() and f.resolve() not in seen:
                seen.add(f.resolve())
                out.append(f)
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("paths", nargs="+", help="Files or directories (*.md), or '-' for stdin -> stdout")
    ap.add_argument("--config", type=Path, default=DEFAULT_CFG, help=f"Dictionary (default: {DEFAULT_CFG})")
    ap.add_argument("--write", action="store_true", help="Apply the AUTO tier in place (default: dry run)")
    args = ap.parse_args(argv)

    if not args.config.exists():
        print(f"error: dictionary not found: {args.config}", file=sys.stderr)
        return 2
    cfg = load(args.config)

    if args.paths == ["-"]:
        if args.write:
            print("error: '-' (stdin) cannot be combined with --write", file=sys.stderr)
            return 2
        new, applied, suggested = apply(sys.stdin.read(), cfg)
        sys.stdout.write(new)
        print(f"replace-words: {len(applied)} replaced, {len(suggested)} to review", file=sys.stderr)
        return 0

    paths = [Path(p) for p in args.paths]
    missing = [p for p in paths if not p.exists()]
    if missing:
        print("error: not found: " + ", ".join(map(str, missing)), file=sys.stderr)
        return 2

    n_auto, n_sugg = len(cfg.get("replacements", [])), len(cfg.get("suggestions", []))
    print(f"# replace-words [{'WRITE' if args.write else 'DRY-RUN'}]")
    print(f"# dictionary: {args.config} (v{cfg.get('version', '?')}, {n_auto} auto, {n_sugg} review)\n")

    files = collect(paths)
    tot_a = tot_s = 0
    for f in files:
        original = f.read_text(encoding="utf-8")
        new, applied, suggested = apply(original, cfg)
        tot_a += len(applied)
        tot_s += len(suggested)
        if not (applied or suggested):
            continue
        print(f"{f}: {len(applied)} replaced, {len(suggested)} to review")
        for ln, found, direct in sorted(applied):
            print(f"  L{ln}: {found!r} -> {direct!r}")
        for ln, found, direct in sorted(suggested):
            print(f"  L{ln}: {found!r} -> maybe {direct!r} (review)")
        if args.write and new != original:
            f.write_text(new, encoding="utf-8")

    print(f"\n{len(files)} file(s), {tot_a} replacement(s), {tot_s} to review")
    if not args.write:
        print("(dry run: re-run with --write to apply the auto tier)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
