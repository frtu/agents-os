#!/usr/bin/env python3
"""List files created/updated since the run baseline (hash-based, not mtime).

Usage:
  python3 changed_files.py --run-dir <dir> [--format json|lines|9log] [--null]

  json  {"created": [...], "updated": [...], "deleted": [...], "pre_dirty_overlap": [...]}
  lines one vault-relative path per line (created + updated) — feed to git add
  9log  "Created: a.md, b.md" / "Updated: c.md" lines for /change-management-9-log

pre_dirty_overlap = changed files that already had uncommitted edits at baseline: staging them
also stages someone else's earlier edits. Report these to the user.
"""

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import wikilib  # noqa: E402


def diff(run_dir):
    base = wikilib.load_json(os.path.join(run_dir, "baseline.json"))
    vault = base["vault"]
    before, now = base["files"], wikilib.snapshot(vault)
    created = sorted(p for p in now if p not in before)
    updated = sorted(p for p in now if p in before and now[p] != before[p])
    deleted = sorted(p for p in before if p not in now)
    dirty = set(base.get("git_dirty", []))
    return {
        "vault": vault,
        "created": created,
        "updated": updated,
        "deleted": deleted,
        "pre_dirty_overlap": sorted(p for p in created + updated if p in dirty),
    }


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-dir", required=True)
    ap.add_argument("--format", choices=("json", "lines", "9log"), default="json")
    ap.add_argument("--null", action="store_true", help="NUL-separate 'lines' output (xargs -0)")
    a = ap.parse_args(argv)
    d = diff(a.run_dir)
    if a.format == "json":
        print(json.dumps(d, indent=2))
    elif a.format == "lines":
        paths = d["created"] + d["updated"]
        sys.stdout.write(("\0" if a.null else "\n").join(paths) + ("" if a.null else "\n"))
    else:
        name = lambda p: os.path.basename(p)  # noqa: E731
        print("Created: " + ", ".join(name(p) for p in d["created"]))
        print("Updated: " + ", ".join(name(p) for p in d["updated"]))
        if d["deleted"]:
            print("Deleted: " + ", ".join(name(p) for p in d["deleted"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
