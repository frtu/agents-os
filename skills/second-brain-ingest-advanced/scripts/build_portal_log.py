#!/usr/bin/env python3
"""Orchestrator-only: turn worker manifests into portal lines and one log entry.

Usage:
  python3 build_portal_log.py --run-dir <dir> --title "<log entry title>" [--summary "<paragraph>"] [--apply]

Without --apply: prints the portal insertions and the log entry (dry run).
With --apply:    inserts portal lines under their section and appends the log entry.

Manifest (one per lane, manifests/<lane>.json):
  {"lane": "members",
   "created": [{"path": "wiki/people/members/a-b.md", "portal_section": "## People > ### Members",
                "hook": "one-line summary"}],
   "updated": [{"path": "wiki/people/members/x.md", "what": "added 2026 section"}],
   "gaps": ["free text: contradictions, [no data] items"]}

portal_section is "## Top" or "## Top > ### Sub". Missing headers are created: a missing
"### Sub" goes at the end of its "## Top" block; a missing "## Top" goes at the end of the file.
Pages whose [[slug]] already appears in the portal are skipped (idempotent).
"""

import argparse
import glob
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import wikilib  # noqa: E402


def slug_of(path):
    return os.path.splitext(os.path.basename(path))[0]


def load_manifests(run_dir, plan):
    order = [l["id"] for p in plan["phases"] for l in p.get("lanes", [])]
    found = {}
    for mp in glob.glob(os.path.join(run_dir, "manifests", "*.json")):
        m = wikilib.load_json(mp)
        found[m.get("lane") or slug_of(mp)] = m
    return [found[k] for k in order if k in found] + [v for k, v in found.items() if k not in order]


def insert_portal(lines, section, entries):
    """lines: list of str without newline. Returns new list."""
    parts = [s.strip() for s in section.split(">")]
    top, sub = parts[0], (parts[1] if len(parts) > 1 else None)

    def block_end(start, level):
        for i in range(start + 1, len(lines)):
            if lines[i].startswith("#") and len(lines[i]) - len(lines[i].lstrip("#")) <= level:
                return i
        return len(lines)

    if top not in lines:
        lines = lines + ["", top, ""]
    t = lines.index(top)
    t_end = block_end(t, top.count("#"))
    target = t
    if sub:
        try:
            target = lines.index(sub, t, t_end)
        except ValueError:
            ins = t_end
            while ins > t + 1 and lines[ins - 1].strip() == "":
                ins -= 1
            lines = lines[:ins] + ["", sub] + lines[ins:]
            target = ins + 1
    end = block_end(target, (sub or top).count("#"))
    last = target
    for i in range(target + 1, end):
        if lines[i].startswith("- "):
            last = i
    pos = last + 1  # after the last list item, or right under the header if the section is empty
    return lines[:pos] + entries + lines[pos:]


def build(run_dir, title, summary="", apply=False):
    plan = wikilib.load_json(os.path.join(run_dir, "plan.json"))
    vault = plan["vault"]
    manifests = load_manifests(run_dir, plan)
    portal_path = os.path.join(vault, "wiki", "portal.md")
    portal = wikilib.read_text(portal_path, "# Portal\n")
    by_section, created_all, updated_all, gaps = {}, [], [], []
    for m in manifests:
        for c in m.get("created", []):
            s = slug_of(c["path"])
            created_all.append((m.get("lane"), s, c.get("hook", "")))
            if c.get("portal_section") and f"[[{s}]]" not in portal and f"[[{s}|" not in portal:
                by_section.setdefault(c["portal_section"], []).append(f"- [[{s}]] — {c.get('hook', '')}".rstrip(" —"))
        for u in m.get("updated", []):
            updated_all.append((slug_of(u["path"]), u.get("what", "")))
        gaps += m.get("gaps", [])

    log = [f"## [{plan.get('date', '')}] ingest | {title}", ""]
    if summary:
        log += [summary, ""]
    log += [f"Trigger: {plan.get('trigger', '')}", ""]
    log += ["**Sources processed:**"] + [f"- `{s}`" for s in sorted({s for p in plan['phases'] for l in p.get('lanes', []) for s in l.get('sources', []) if s.startswith('raw/')})] + [""]
    lanes_seen = []
    for lane, _, _ in created_all:
        if lane not in lanes_seen:
            lanes_seen.append(lane)
    log.append(f"**Pages created ({len(created_all)}):**")
    for lane in lanes_seen:
        items = [f"[[{s}]]" for l, s, _ in created_all if l == lane]
        log.append(f"- {lane}: " + ", ".join(items))
    log += ["", f"**Pages updated ({len(updated_all)}):**"]
    log += [f"- [[{s}]] — {w}".rstrip(" —") for s, w in updated_all]
    if gaps:
        log += ["", "**Open contradictions / gaps:**"] + [f"- {g}" for g in gaps]
    entry = "\n".join(log) + "\n"

    if apply:
        lines = portal.rstrip("\n").split("\n")
        for section, entries in by_section.items():
            lines = insert_portal(lines, section, entries)
        with open(portal_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
        log_path = os.path.join(vault, "wiki", "log.md")
        prev = wikilib.read_text(log_path, "# Log\n")
        with open(log_path, "w", encoding="utf-8") as f:
            f.write(prev.rstrip("\n") + "\n\n" + entry)
    return by_section, entry


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-dir", required=True)
    ap.add_argument("--title", required=True)
    ap.add_argument("--summary", default="")
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args(argv)
    by_section, entry = build(a.run_dir, a.title, a.summary, a.apply)
    print("# Portal insertions" + ("" if a.apply else " (dry run)"))
    for section, entries in by_section.items():
        print(f"\n{section}")
        print("\n".join(entries))
    print("\n# Log entry" + ("" if a.apply else " (dry run)") + "\n")
    print(entry)
    return 0


if __name__ == "__main__":
    sys.exit(main())
