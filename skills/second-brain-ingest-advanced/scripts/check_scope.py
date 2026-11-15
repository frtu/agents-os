#!/usr/bin/env python3
"""Gate after a phase: did every worker stay in its lane and deliver its contract?

Usage: python3 check_scope.py --run-dir <dir> --upto <phase-id> [--orchestrator-done]

Checks, for all phases up to and including --upto:
  OUT_OF_SCOPE   a changed file sits in no lane's write_scope                 -> exit 1
  OWNED_TOUCHED  an orchestrator-owned file changed (skip with --orchestrator-done) -> exit 1
  NOT_CREATED    a slug the plan assigned was not created                     -> exit 1
  NO_MANIFEST    a lane did not write manifests/<lane>.json                   -> exit 1
  BAD_MANIFEST   manifest unreadable or missing 'created'/'updated' lists     -> exit 1
  PRE_DIRTY      changed file already had uncommitted edits at baseline       (warning)
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import wikilib  # noqa: E402
import changed_files  # noqa: E402


def lanes_upto(plan, upto):
    out = []
    for p in plan["phases"]:
        out += p.get("lanes", [])
        if p["id"] == upto:
            return out
    raise SystemExit(f"ERROR: phase {upto} not in plan")


def check(run_dir, upto, orchestrator_done=False):
    plan = wikilib.load_json(os.path.join(run_dir, "plan.json"))
    d = changed_files.diff(run_dir)
    vault = d["vault"]
    lanes = lanes_upto(plan, upto)
    owned = plan.get("orchestrator_owned", [])
    errors, warnings = [], []
    for f in d["created"] + d["updated"]:
        if f in owned:
            if not orchestrator_done:
                errors.append(f"OWNED_TOUCHED: {f}")
            continue
        if not any(wikilib.in_scope(f, l.get("write_scope", [])) for l in lanes):
            errors.append(f"OUT_OF_SCOPE: {f}")
    for lane in lanes:
        for c in lane.get("creates", []):
            p = f"{c['dir'].rstrip('/')}/{c['slug']}.md"
            if not os.path.exists(os.path.join(vault, p)):
                errors.append(f"NOT_CREATED: {p} (lane {lane['id']})")
        mp = os.path.join(run_dir, "manifests", f"{lane['id']}.json")
        if not os.path.exists(mp):
            errors.append(f"NO_MANIFEST: {lane['id']}")
            continue
        try:
            m = wikilib.load_json(mp)
            if not isinstance(m.get("created"), list) or not isinstance(m.get("updated"), list):
                raise ValueError("created/updated must be lists")
        except (ValueError, OSError) as e:
            errors.append(f"BAD_MANIFEST: {lane['id']}: {e}")
    for f in d["pre_dirty_overlap"]:
        warnings.append(f"PRE_DIRTY: {f}")
    return errors, warnings


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-dir", required=True)
    ap.add_argument("--upto", required=True)
    ap.add_argument("--orchestrator-done", action="store_true")
    a = ap.parse_args(argv)
    errors, warnings = check(a.run_dir, a.upto, a.orchestrator_done)
    for w in warnings:
        print(f"WARN {w}")
    for e in errors:
        print(e)
    print(f"{'FAIL' if errors else 'OK'}: {len(errors)} errors, {len(warnings)} warnings")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
