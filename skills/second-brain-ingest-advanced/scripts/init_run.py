#!/usr/bin/env python3
"""Phase 0 — create a run folder: baseline snapshot, existing-page inventory, extracted sources,
and a plan skeleton.

Usage:
  python3 init_run.py --vault <vault-dir> --run-dir <dir> --trigger "<user instruction>" \
      --source raw/a.pdf --source "raw/b c.md" [--date YYYY-MM-DD]

Writes into <run-dir>:
  baseline.json   sha1 of every wiki/ + output/ markdown file, and git-dirty paths at start
  inventory.json  existing slugs per wiki folder + portal headers (dedup brief for workers)
  sources.json    each source: path, kind, line count, extracted text path
  extracted/      PDF text (pypdf if installed), whitespace-normalised
  plan.json       skeleton to fill (only if absent)
  briefs/ manifests/
"""

import argparse
import datetime
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import wikilib  # noqa: E402


def normalise_pdf_text(text):
    """PDF exports often put one word per line (word \\n \\n word). Re-join them."""
    text = text.replace("\r", "")
    text = re.sub(r"[ \t]*\n[ \t]*\n[ \t]*(?=\S)", " ", text)  # word / blank / word -> word word
    text = re.sub(r"[ \t]{2,}", " ", text)
    return text.strip() + "\n"


def extract_pdf(path):
    try:
        import pypdf  # type: ignore
    except ImportError:
        return None, "pypdf not installed: read the PDF directly"
    reader = pypdf.PdfReader(path)
    pages = [normalise_pdf_text(p.extract_text() or "") for p in reader.pages]
    return "\n--- page ---\n".join(pages), f"{len(reader.pages)} pages"


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--vault", required=True)
    ap.add_argument("--run-dir", required=True)
    ap.add_argument("--trigger", required=True)
    ap.add_argument("--source", action="append", default=[])
    ap.add_argument("--date", default=datetime.date.today().isoformat())
    a = ap.parse_args(argv)

    vault, run = a.vault, a.run_dir
    if not os.path.isdir(os.path.join(vault, "wiki")):
        print(f"ERROR: {vault} has no wiki/ folder", file=sys.stderr)
        return 2
    for d in ("extracted", "briefs", "manifests"):
        os.makedirs(os.path.join(run, d), exist_ok=True)

    wikilib.save_json(os.path.join(run, "baseline.json"), {
        "date": a.date,
        "vault": os.path.abspath(vault),
        "files": wikilib.snapshot(vault),
        "git_dirty": wikilib.git_dirty(vault),
    })

    portal = os.path.join(vault, "wiki", "portal.md")
    headers = []
    if os.path.exists(portal):
        with open(portal, encoding="utf-8") as f:
            headers = [l.rstrip() for l in f if l.startswith("#")]
    wikilib.save_json(os.path.join(run, "inventory.json"), {
        "slugs": wikilib.slug_index(vault),
        "portal_headers": headers,
    })

    sources, missing = [], []
    for s in a.source:
        p = s if os.path.isabs(s) else os.path.join(vault, s)
        if not os.path.exists(p):
            missing.append(s)
            continue
        entry = {"path": wikilib.rel(vault, p), "kind": os.path.splitext(p)[1].lstrip(".").lower()}
        if entry["kind"] == "pdf":
            text, note = extract_pdf(p)
            entry["note"] = note
            if text is not None:
                out = os.path.join(run, "extracted", os.path.splitext(os.path.basename(p))[0] + ".txt")
                with open(out, "w", encoding="utf-8") as f:
                    f.write(text)
                entry["extracted"] = os.path.abspath(out)
                entry["lines"] = text.count("\n")
        else:
            with open(p, encoding="utf-8", errors="replace") as f:
                entry["lines"] = sum(1 for _ in f)
        sources.append(entry)
    wikilib.save_json(os.path.join(run, "sources.json"), sources)

    plan_path = os.path.join(run, "plan.json")
    if not os.path.exists(plan_path):
        wikilib.save_json(plan_path, {
            "run_id": os.path.basename(os.path.abspath(run)),
            "date": a.date,
            "vault": os.path.abspath(vault),
            "trigger": a.trigger,
            "target_system": "",
            "orchestrator_owned": ["wiki/portal.md", "wiki/log.md"],
            "phases": [
                {"id": "1-atomic", "parallel": True, "lanes": []},
                {"id": "2-bubble-up", "parallel": True, "lanes": []},
                {"id": "3-deliverable", "parallel": False, "lanes": []},
            ],
        })

    print(f"run dir: {os.path.abspath(run)}")
    print(f"baseline: {len(wikilib.snapshot(vault))} markdown files; "
          f"git-dirty at start: {len(wikilib.git_dirty(vault))}")
    for s in sources:
        print(f"source: {s['path']} ({s['kind']}, {s.get('lines', '?')} lines"
              f"{', ' + s['note'] if s.get('note') else ''})")
    for m in missing:
        print(f"MISSING SOURCE: {m}", file=sys.stderr)
    return 1 if missing else 0


if __name__ == "__main__":
    sys.exit(main())
