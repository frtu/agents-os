#!/usr/bin/env python3
"""Validate plan.json — the slug contract that makes parallel writers safe.

Usage: python3 validate_plan.py --run-dir <dir> [--templates <references/templates>]

Checks (exit 1 on any ERROR):
  - lane ids unique; every lane has template, sources, write_scope
  - every created slug is kebab-case, unique across the whole plan, and does not already
    exist in the vault (inventory.json) — existing pages go in `updates`, not `creates`
  - every created page and every update path lies inside the lane's write_scope
  - lanes of the same parallel phase have disjoint write scopes (no two writers per file)
  - no lane scope covers an orchestrator-owned file (portal, log)
  - every `updates` path exists in the vault (when the vault dir exists)
  - each template file exists (when --templates is given)
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import wikilib  # noqa: E402

REQUIRED = ("id", "template", "sources", "write_scope")


def validate(plan, inventory, templates_dir=None):
    errors, warnings = [], []
    existing = {s for slugs in inventory.get("slugs", {}).values() for s in slugs}
    owned = plan.get("orchestrator_owned", [])
    seen_lanes, seen_slugs = set(), {}

    for phase in plan.get("phases", []):
        lanes = phase.get("lanes", [])
        for lane in lanes:
            lid = lane.get("id", "?")
            for k in REQUIRED:
                if k not in lane:
                    errors.append(f"{lid}: missing '{k}'")
            if lid in seen_lanes:
                errors.append(f"{lid}: duplicate lane id")
            seen_lanes.add(lid)
            scope = lane.get("write_scope", [])
            for o in owned:
                if wikilib.in_scope(o, scope):
                    errors.append(f"{lid}: write_scope covers orchestrator-owned {o}")
            if templates_dir and "template" in lane:
                if not os.path.exists(os.path.join(templates_dir, lane["template"] + ".md")):
                    errors.append(f"{lid}: template '{lane['template']}' not found")
            for c in lane.get("creates", []):
                slug, d = c.get("slug", ""), c.get("dir", "").rstrip("/")
                if not wikilib.SLUG.match(slug):
                    errors.append(f"{lid}: slug '{slug}' is not kebab-case")
                if slug in seen_slugs:
                    errors.append(f"{lid}: slug '{slug}' also created by {seen_slugs[slug]}")
                seen_slugs[slug] = lid
                if slug in existing:
                    errors.append(f"{lid}: slug '{slug}' already exists — move it to 'updates'")
                if not wikilib.in_scope(f"{d}/{slug}.md", scope):
                    errors.append(f"{lid}: {d}/{slug}.md is outside write_scope")
            for u in lane.get("updates", []):
                vault = plan.get("vault", "")
                if os.path.isdir(vault) and not os.path.exists(os.path.join(vault, u)):
                    errors.append(f"{lid}: update target {u} does not exist — move it to 'creates'")
                if not wikilib.in_scope(u, scope):
                    errors.append(f"{lid}: update {u} is outside write_scope")
            if not lane.get("creates") and not lane.get("updates"):
                warnings.append(f"{lid}: declares no creates and no updates")
        if phase.get("parallel"):
            for i, x in enumerate(lanes):
                for y in lanes[i + 1:]:
                    if wikilib.scopes_overlap(x.get("write_scope", []), y.get("write_scope", [])):
                        errors.append(f"phase {phase.get('id')}: {x.get('id')} and {y.get('id')} "
                                      f"have overlapping write_scope")
    if not plan.get("target_system"):
        warnings.append("target_system is empty — state the vault's purpose in one sentence")
    return errors, warnings


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-dir", required=True)
    ap.add_argument("--templates")
    a = ap.parse_args(argv)
    plan = wikilib.load_json(os.path.join(a.run_dir, "plan.json"))
    inv_path = os.path.join(a.run_dir, "inventory.json")
    inventory = wikilib.load_json(inv_path) if os.path.exists(inv_path) else {}
    errors, warnings = validate(plan, inventory, a.templates)
    for w in warnings:
        print(f"WARN: {w}")
    for e in errors:
        print(f"ERROR: {e}")
    n = sum(len(p.get("lanes", [])) for p in plan.get("phases", []))
    print(f"{'INVALID' if errors else 'OK'}: {n} lanes, {len(errors)} errors, {len(warnings)} warnings")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
