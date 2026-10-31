#!/usr/bin/env python3
"""Tests for scan_inbox.py — run with: python3 -m unittest test_scan_inbox.py -v"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(HERE, "scan_inbox.py")


class TestScanInbox(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="inbox-test-")
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)

    def vault(self, name, transcripts, layout="vault"):
        """Create a vault with transcripts. transcripts = [(relpath, content)]."""
        base = os.path.join(self.tmp, name, layout if layout == "vault" else "")
        tr = os.path.join(base, "raw", "transcripts")
        for rel, content in transcripts:
            p = os.path.join(tr, rel)
            os.makedirs(os.path.dirname(p), exist_ok=True)
            with open(p, "w") as f:
                f.write(content)
        return os.path.join(self.tmp, name)

    def run_scan(self, *extra):
        r = subprocess.run(
            [sys.executable, SCRIPT, self.tmp, "--json"] + list(extra),
            capture_output=True, text=True,
        )
        self.assertEqual(r.returncode, 0, r.stderr)
        return json.loads(r.stdout)

    def test_uncopied_and_copied(self):
        self.vault("global-inbox", [
            ("2026-10-01 Alpha.md", "a"),
            ("2026-10-02 Beta.md", "b"),
            ("topic/2026-10-03 Gamma.md", "c"),
        ])
        # target with vault/ layout, has Alpha copied at root of transcripts
        self.vault("search-x", [("2026-10-01 Alpha.md", "a")])
        data = self.run_scan()
        files = {r["file"]: r for r in data["rows"]}
        self.assertEqual(files["2026-10-01 Alpha.md"]["status"], "copied")
        self.assertEqual(files["2026-10-01 Alpha.md"]["target"], "search-x")
        self.assertEqual(files["2026-10-02 Beta.md"]["status"], "NOT COPIED")
        # category shows only sub-path after raw/transcripts
        self.assertEqual(files["2026-10-03 Gamma.md"]["origin_category"], "topic")

    def test_flat_layout_target(self):
        """Target vaults that keep raw/ at the top level (no vault/ wrapper)."""
        self.vault("global-inbox", [("2026-10-01 Alpha.md", "a")])
        self.vault("workflow", [("2026-10-01 Alpha.md", "a")], layout="flat")
        data = self.run_scan()
        self.assertEqual(data["rows"][0]["target"], "workflow")

    def test_fuzzy_match_ignores_date_and_case(self):
        self.vault("global-inbox", [("2026-10-05 InterviewJeremy.md", "a")])
        self.vault("interviews", [("2026-10-06 interviewJeremy.md", "b")])
        data = self.run_scan()
        self.assertEqual(data["rows"][0]["status"], "copied")

    def test_ignores_underscore_and_hidden_folders(self):
        os.makedirs(os.path.join(self.tmp, "_Template_"), exist_ok=True)
        os.makedirs(os.path.join(self.tmp, ".hidden"), exist_ok=True)
        self.vault("global-inbox", [("2026-10-01 Alpha.md", "a")])
        data = self.run_scan()
        self.assertEqual(data["rows"][0]["target"], "")

    def test_orphans_reported(self):
        self.vault("global-inbox", [("2026-10-01 Alpha.md", "a")])
        self.vault("search-x", [("2019-01-01 Only-In-Target.md", "b")])
        data = self.run_scan()
        self.assertEqual(len(data["orphans"]), 1)
        self.assertEqual(data["orphans"][0]["target"], "search-x")

    def test_non_md_ignored(self):
        self.vault("global-inbox", [("2026-10-01 Notes.txt", "a")])
        data = self.run_scan()
        self.assertEqual(data["rows"], [])


if __name__ == "__main__":
    unittest.main()
