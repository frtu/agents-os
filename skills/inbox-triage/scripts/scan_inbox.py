#!/usr/bin/env python3
"""Scan workspace vaults for transcripts and report origin→target copy state.

Origin vault is the folder whose name matches --origin (default: global-inbox).
Every other folder in the root is a target vault. For each transcript found in
the origin vault, checks whether a same-named file exists in a target vault
under raw/transcripts (by filename, any depth, .md only).

Prints a markdown table: origin vault | target vault | category (sub-path under
raw/transcripts) | file | copy status. Only the sub-path after raw/transcripts
is shown as the category.
"""

import argparse
import json
import os
import re
import sys

TRANSCRIPT_EXTS = (".md",)

# Filename prefixes that are date-stamps, e.g. "2026-10-21 " or "2026-10-21 "
DATE_PREFIX_RE = re.compile(r"^\d{4}-\d{2}-\d{2}\s*")


def strip_date(name):
    return DATE_PREFIX_RE.sub("", name).strip()


def norm_key(name):
    """Case/spacing-insensitive key for fuzzy matching."""
    return strip_date(os.path.splitext(name)[0]).lower().replace("-", " ").replace("_", " ").replace("  ", " ").strip()


def is_transcript(name):
    return os.path.splitext(name)[1].lower() in TRANSCRIPT_EXTS


def list_vaults(root, origin):
    try:
        entries = sorted(os.listdir(root))
    except OSError as e:
        sys.exit(f"error: cannot list root {root}: {e}")
    vaults = []
    for e in entries:
        p = os.path.join(root, e)
        if e.startswith(".") or e.startswith("_") or not os.path.isdir(p):
            continue
        if e == origin:
            continue
        vaults.append(e)
    return vaults


def find_transcripts(base):
    """Yield (relpath_after_raw_transcripts, full_path) for transcripts under base/raw/transcripts."""
    tr = os.path.join(base, "raw", "transcripts")
    out = []
    if not os.path.isdir(tr):
        return out
    for dirpath, _dirnames, filenames in os.walk(tr):
        for fn in filenames:
            if not is_transcript(fn):
                continue
            full = os.path.join(dirpath, fn)
            rel = os.path.relpath(full, tr)
            out.append((rel, full))
    out.sort()
    return out


def index_target(target_root):
    """target_root is the vault folder; search <vault>/raw/transcripts and <vault>/vault/raw/transcripts."""
    idx = {}  # norm_key -> (relpath, fullpath)
    for base in (os.path.join(target_root, "vault"), target_root):
        for rel, full in find_transcripts(base):
            k = norm_key(os.path.basename(rel))
            if k and k not in idx:
                idx[k] = (rel, full)
    return idx


def count_target(target_root):
    n = 0
    for base in (os.path.join(target_root, "vault"), target_root):
        n += len(find_transcripts(base))
    return n


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("root", nargs="?",
                    default=os.environ.get("WORKSPACES_ROOT", "~/Workspaces"),
                    help="Workspace root containing one folder per vault")
    ap.add_argument("--origin", default="global-inbox", help="Origin vault folder name")
    ap.add_argument("--json", action="store_true", help="Emit JSON instead of a markdown table")
    ap.add_argument("--copy-cmds", action="store_true",
                    help="Additionally print ready-to-run cp commands for uncopied files")
    args = ap.parse_args()

    root = os.path.expanduser(args.root)
    origin_path = os.path.join(root, args.origin)
    if not os.path.isdir(origin_path):
        sys.exit(f"error: origin vault not found: {origin_path}")

    vaults = list_vaults(root, args.origin)

    # Index target vaults: vault name -> norm_key index + transcript count
    targets = {}
    for v in vaults:
        vpath = os.path.join(root, v)
        targets[v] = {
            "index": index_target(vpath),
            "count": count_target(vpath),
        }

    origin_files = find_transcripts(os.path.join(origin_path, "vault")) + \
        find_transcripts(origin_path)

    rows = []
    copied_keys = set()
    for rel, full in origin_files:
        key = norm_key(os.path.basename(rel))
        category = os.path.dirname(rel)
        matched = None
        for v in vaults:
            if key in targets[v]["index"]:
                matched = v
                copied_keys.add(key)
                break
        rows.append({
            "origin_category": category if category and category != "." else "(root)",
            "file": os.path.basename(rel),
            "target": matched or "",
            "status": "copied" if matched else "NOT COPIED",
        })

    # Transcripts sitting in target vaults that have no origin counterpart (reverse check)
    orphans = []
    origin_keys = {norm_key(os.path.basename(rel)) for rel, _ in origin_files}
    for v in vaults:
        for k, (rel, _full) in targets[v]["index"].items():
            if k not in origin_keys:
                orphans.append({"target": v, "path": rel})

    if args.json:
        print(json.dumps({"rows": rows, "orphans": orphans}, indent=2))
        return

    # Markdown table
    print("| Origin category | File | Target vault | Status |")
    print("| --- | --- | --- | --- |")
    for r in rows:
        tgt = r["target"] or "—"
        print(f"| {r['origin_category']} | {r['file']} | {tgt} | {r['status']} |")

    n_copied = sum(1 for r in rows if r["status"] == "copied")
    n_pending = sum(1 for r in rows if r["status"] == "NOT COPIED")
    print()
    print(f"Origin: {args.origin} ({len(rows)} transcripts) · copied: {n_copied} · not copied: {n_pending}")

    if args.copy_cmds and n_pending:
        print()
        print("```bash")
        for r in rows:
            if r["status"] != "NOT COPIED":
                continue
            src = os.path.join(args.origin, "vault", "raw", "transcripts", r["origin_category"], r["file"])
            src = os.path.normpath(src)
            print(f"cp \"{src}\" \"<{r['origin_category'] or 'root'} target vault>/raw/transcripts/\"")
        print("```")

    if orphans:
        print()
        print(f"### In target vaults but not in origin ({len(orphans)})")
        print()
        print("| Target vault | Path under raw/transcripts |")
        print("| --- | --- |")
        for o in orphans:
            print(f"| {o['target']} | {o['path']} |")


if __name__ == "__main__":
    main()
