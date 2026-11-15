#!/usr/bin/env python3
"""Render one worker brief per lane of a phase from the brief templates.

Usage: python3 render_briefs.py --run-dir <dir> --phase 1-atomic --templates <references/templates>

Each template may use these placeholders:
  {{VAULT}} {{RUN_DIR}} {{LANE_ID}} {{PHASE_ID}} {{TARGET_SYSTEM}} {{DATE}}
  {{SOURCES}}        bullet list of the lane's sources (with extracted-text path when known)
  {{WRITE_SCOPE}}    bullet list of paths the lane may create/modify
  {{CREATES}}        bullet list of slugs this lane must create (dir/slug.md)
  {{UPDATES}}        bullet list of existing files this lane may update
  {{SIBLING_SLUGS}}  slugs other lanes (this phase and earlier ones) create — link to them exactly
  {{FORBIDDEN}}      orchestrator-owned files + every other lane's scope
  {{INSTRUCTIONS}}   lane-specific instructions from plan.json
  {{MANIFEST_PATH}}  where the worker must write its JSON manifest
  {{INVENTORY_PATH}} inventory.json (existing slugs — dedup filter)
Writes <run-dir>/briefs/<phase>--<lane>.md and prints the paths.
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import wikilib  # noqa: E402


def bullets(items, empty="- (none)"):
    return "\n".join(f"- {i}" for i in items) if items else empty


def render(plan, phase_id, lane, sources_meta, run_dir):
    phases = plan["phases"]
    idx = next(i for i, p in enumerate(phases) if p["id"] == phase_id)
    siblings, forbidden = [], list(plan.get("orchestrator_owned", []))
    for p in phases[: idx + 1]:
        for other in p["lanes"]:
            if other["id"] == lane["id"]:
                continue
            siblings += [f"[[{c['slug']}]] ({c['dir'].rstrip('/')}, lane {other['id']})"
                         for c in other.get("creates", [])]
            if p["id"] == phase_id:
                forbidden += other.get("write_scope", [])
    meta = {m["path"]: m for m in sources_meta}
    src = []
    for s in lane.get("sources", []):
        m = meta.get(s, {})
        src.append(f"{s}" + (f" — extracted text: {m['extracted']}" if m.get("extracted") else ""))
    return {
        "VAULT": plan["vault"],
        "RUN_DIR": os.path.abspath(run_dir),
        "LANE_ID": lane["id"],
        "PHASE_ID": phase_id,
        "TARGET_SYSTEM": plan.get("target_system", ""),
        "DATE": plan.get("date", ""),
        "SOURCES": bullets(src),
        "WRITE_SCOPE": bullets(lane.get("write_scope", [])),
        "CREATES": bullets([f"{c['dir'].rstrip('/')}/{c['slug']}.md" + (f" — {c['hint']}" if c.get("hint") else "")
                            for c in lane.get("creates", [])]),
        "UPDATES": bullets(lane.get("updates", [])),
        "SIBLING_SLUGS": bullets(siblings),
        "FORBIDDEN": bullets(sorted(set(forbidden))),
        "INSTRUCTIONS": lane.get("instructions", "").strip() or "(none)",
        "MANIFEST_PATH": os.path.join(os.path.abspath(run_dir), "manifests", f"{lane['id']}.json"),
        "INVENTORY_PATH": os.path.join(os.path.abspath(run_dir), "inventory.json"),
    }


def fill(template, values):
    for k, v in values.items():
        template = template.replace("{{" + k + "}}", v)
    return template


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-dir", required=True)
    ap.add_argument("--phase", required=True)
    ap.add_argument("--templates", required=True)
    a = ap.parse_args(argv)
    plan = wikilib.load_json(os.path.join(a.run_dir, "plan.json"))
    sp = os.path.join(a.run_dir, "sources.json")
    sources_meta = wikilib.load_json(sp) if os.path.exists(sp) else []
    phase = next((p for p in plan["phases"] if p["id"] == a.phase), None)
    if phase is None:
        print(f"ERROR: phase {a.phase} not in plan", file=sys.stderr)
        return 2
    os.makedirs(os.path.join(a.run_dir, "briefs"), exist_ok=True)
    for lane in phase["lanes"]:
        with open(os.path.join(a.templates, lane["template"] + ".md"), encoding="utf-8") as f:
            text = fill(f.read(), render(plan, a.phase, lane, sources_meta, a.run_dir))
        out = os.path.join(a.run_dir, "briefs", f"{a.phase}--{lane['id']}.md")
        with open(out, "w", encoding="utf-8") as f:
            f.write(text)
        print(out)
    if phase.get("parallel"):
        print(f"# {len(phase['lanes'])} briefs — launch them in parallel")
    return 0


if __name__ == "__main__":
    sys.exit(main())
