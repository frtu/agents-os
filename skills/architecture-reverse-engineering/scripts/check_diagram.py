#!/usr/bin/env python3
"""
check_diagram — gate: validate a generated component-diagram document.

Checks, in order:
  MISSING_SECTION  a '##' heading of the template skeleton is not in the doc
  NO_MERMAID       the doc has no ```mermaid block
  UNBALANCED       a Mermaid block has more 'subgraph' than 'end' (or the reverse)
  DUP_ID           a node id is defined twice with different labels
  UNQUOTED_CHARS   an unquoted node label contains ( ) [ ] { }
  UNKNOWN_CLASS    a 'class' / ':::' uses a classDef that isn't defined
  MISSING_EVIDENCE a backticked path in the doc doesn't exist in the repo (needs --repo)

The required headings come from the template (default:
references/templates/component-diagram.md), so editing the template changes
the gate with no code change. Headings are compared case-insensitively, with
[bracketed] guidance removed.

    python3 check_diagram.py <doc.md> [--repo <root>] [--template FILE] [--json]

Exit code: 0 = no findings, 1 = findings (listed on stdout), 2 = bad arguments
or the doc / template / repo can't be read.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import arch_lib as lib

SCRIPTS_DIR = Path(__file__).resolve().parent
DEFAULT_SIGNALS = SCRIPTS_DIR.parent / "config" / "signals.json"
DEFAULT_TEMPLATE = SCRIPTS_DIR.parent / "references" / "templates" / "component-diagram.md"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("doc", help="the generated Markdown document")
    ap.add_argument("--repo", default=None,
                    help="repo root: check that every cited path exists (default: skip that check)")
    ap.add_argument("--template", default=str(DEFAULT_TEMPLATE),
                    help="template whose '##' headings are required (default: the skill's template)")
    ap.add_argument("--json", action="store_true", help="print findings as JSON (for agents)")
    return ap.parse_args(argv)


def check_sections(md: str, template: str) -> list[lib.Finding]:
    have = set(lib.doc_headings(md))
    return [lib.Finding("MISSING_SECTION", 0, f"missing section '## {h}'")
            for h in lib.template_headings(template) if h not in have]


def check_mermaid(md: str) -> list[lib.Finding]:
    blocks = lib.mermaid_blocks(md)
    if not blocks:
        return [lib.Finding("NO_MERMAID", 0, "no ```mermaid block")]
    out = []
    for start, body in blocks:
        out.extend(lib.lint_mermaid(body, start))
    return out


def repo_index(root: Path) -> tuple[set[str], set[str]]:
    """All repo-relative paths (files and dirs) and all basenames, honouring skip_dirs."""
    compiled = lib.compile_signals(lib.load_signals(DEFAULT_SIGNALS))
    paths, names = set(), set()
    for rel, _ in lib.iter_repo_files(root, compiled):
        paths.add(rel)
        names.add(rel.rsplit("/", 1)[-1])
        parts = rel.split("/")
        for i in range(1, len(parts)):
            paths.add("/".join(parts[:i]))
            names.add(parts[i - 1])
    return paths, names


def check_evidence(md: str, root: Path) -> list[lib.Finding]:
    paths, names = repo_index(root)
    out = []
    for lineno, token in lib.cited_paths(md):
        clean = token.rstrip("/").removeprefix("./")
        if clean in paths or ("/" not in clean and clean in names):
            continue
        if (root / clean).exists():                 # skipped dirs (build/) or skipped files
            continue
        out.append(lib.Finding("MISSING_EVIDENCE", lineno, f"cited path not in repo: {token}"))
    return out


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    doc, template = Path(args.doc).expanduser(), Path(args.template).expanduser()
    try:
        md = doc.read_text(encoding="utf-8")
        tpl = template.read_text(encoding="utf-8")
    except OSError as exc:
        print(f"check_diagram: {exc}", file=sys.stderr)
        return 2
    findings = check_sections(md, tpl) + check_mermaid(md)
    if args.repo:
        root = Path(args.repo).expanduser()
        if not root.is_dir():
            print(f"check_diagram: not a directory: {root}", file=sys.stderr)
            return 2
        findings += check_evidence(md, root.resolve())
    if args.json:
        print(json.dumps({"doc": str(doc), "ok": not findings,
                          "findings": [vars(f) for f in findings]},
                         ensure_ascii=False, indent=2))
    elif findings:
        for f in findings:
            where = f"{doc.name}:{f.line}" if f.line else doc.name
            print(f"{f.code}  {where}  {f.message}")
    else:
        print(f"OK  {doc}")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
