"""Test fixture: a tiny vault + run dir. Imported by the test_*.py files."""

import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import wikilib  # noqa: E402

PORTAL = """# Portal

## Concepts

### Patterns
- [[old-pattern]] — existing

## People

### Members
- [[alice]] — existing member
"""


def make_vault(tc, name="demo"):
    """Create <tmp>/<name>/vault with wiki pages; register cleanup on the TestCase."""
    tmp = tempfile.mkdtemp(prefix="sbia-test-")
    tc.addCleanup(shutil.rmtree, tmp, ignore_errors=True)
    vault = os.path.join(tmp, name, "vault")
    files = {
        "wiki/portal.md": PORTAL,
        "wiki/log.md": "# Log\n\n## [2026-01-01] ingest | first\n",
        "wiki/concepts/patterns/old-pattern.md": "# Old\nSee [[alice]].\n",
        "wiki/people/members/alice.md": "# Alice\n",
        "raw/notes/source.md": "line1\nline2\n",
    }
    for p, c in files.items():
        write(vault, p, c)
    return vault, os.path.join(tmp, "run")


def write(vault, path, content):
    full = os.path.join(vault, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8") as f:
        f.write(content)


def run(script, *args):
    return subprocess.run([sys.executable, os.path.join(HERE, script), *args],
                          capture_output=True, text=True)


def init(tc, vault, run_dir):
    r = run("init_run.py", "--vault", vault, "--run-dir", run_dir, "--trigger", "test ingest",
            "--source", "raw/notes/source.md", "--date", "2026-02-02")
    tc.assertEqual(r.returncode, 0, r.stderr)


def plan_with(run_dir, lanes_by_phase, target="demo system"):
    plan = wikilib.load_json(os.path.join(run_dir, "plan.json"))
    plan["target_system"] = target
    for p in plan["phases"]:
        p["lanes"] = lanes_by_phase.get(p["id"], [])
    wikilib.save_json(os.path.join(run_dir, "plan.json"), plan)
    return plan


def lane(lid, scope, creates=(), updates=(), template="brief-atomic"):
    return {"id": lid, "template": template, "sources": ["raw/notes/source.md"],
            "write_scope": list(scope),
            "creates": [{"slug": s, "dir": d} for d, s in creates],
            "updates": list(updates), "instructions": f"do {lid}"}
