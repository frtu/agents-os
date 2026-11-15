#!/usr/bin/env python3
"""Gate: every same-vault wikilink in the changed files resolves.

Usage:
  python3 check_links.py --run-dir <dir> [--fix-abspath]      # files changed since baseline
  python3 check_links.py --vault <vault> --file wiki/a.md ...  # explicit files

Findings:
  MISSING  target page does not exist in this vault            -> exit 1
  ABSPATH  link spells this vault's own path (Vault/x/wiki/.../slug) instead of the slug;
           --fix-abspath rewrites it to [[slug|Display]]
Links that contain '/' and do not resolve in this vault are cross-vault links: exempt.
"""

import argparse
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import wikilib  # noqa: E402
import changed_files  # noqa: E402


def check(vault, files, fix_abspath=False):
    targets = wikilib.link_targets(vault)
    vname = wikilib.vault_name(vault)
    findings = []
    for f in files:
        path = os.path.join(vault, f)
        if not f.endswith(".md") or not os.path.exists(path):
            continue
        with open(path, encoding="utf-8") as fh:
            text = fh.read()
        new_text = text
        for m in wikilib.WIKILINK.finditer(text):
            raw = m.group(1)
            target = wikilib.parse_link(raw)
            if not target:
                continue
            if "/" in target:
                base = target.rsplit("/", 1)[1]
                own = f"/{vname}/" in f"/{target}" and base in targets
                if own:
                    findings.append(("ABSPATH", f, target))
                    if fix_abspath:
                        fixed = raw.replace(target, base, 1)
                        new_text = new_text.replace(f"[[{raw}]]", f"[[{fixed}]]")
                continue  # cross-vault: exempt
            if target not in targets:
                findings.append(("MISSING", f, target))
        if fix_abspath and new_text != text:
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(new_text)
    return findings


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-dir")
    ap.add_argument("--vault")
    ap.add_argument("--file", action="append", default=[])
    ap.add_argument("--fix-abspath", action="store_true")
    a = ap.parse_args(argv)
    if a.run_dir:
        d = changed_files.diff(a.run_dir)
        vault, files = d["vault"], d["created"] + d["updated"]
    elif a.vault:
        vault, files = a.vault, a.file
    else:
        ap.error("--run-dir or --vault is required")
    findings = check(vault, files, a.fix_abspath)
    for kind, f, target in findings:
        print(f"{kind}: [[{target}]] in {f}")
    missing = sum(1 for k, _, _ in findings if k == "MISSING")
    print(f"{'FAIL' if missing else 'OK'}: {len(files)} files checked, {missing} missing, "
          f"{len(findings) - missing} abspath{' (fixed)' if a.fix_abspath else ''}")
    return 1 if missing else 0


if __name__ == "__main__":
    sys.exit(main())
