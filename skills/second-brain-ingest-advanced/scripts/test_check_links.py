#!/usr/bin/env python3
"""Tests for check_links.py — run with: python3 -m unittest test_check_links.py -v"""

import unittest

import _fixture as fx
import check_links


class TestCheckLinks(unittest.TestCase):
    def setUp(self):
        self.vault, self.run = fx.make_vault(self, name="demo")
        fx.init(self, self.vault, self.run)

    def test_missing_and_resolving_links(self):
        fx.write(self.vault, "wiki/people/members/bob.md",
                 "[[alice]] [[alice#Role|Alice]] | [[old-pattern\\|Old]] [[ghost]] [[Other/vault/wiki/x|X]]\n")
        f = check_links.check(self.vault, ["wiki/people/members/bob.md"])
        self.assertEqual(f, [("MISSING", "wiki/people/members/bob.md", "ghost")])
        r = fx.run("check_links.py", "--run-dir", self.run)
        self.assertEqual(r.returncode, 1)
        self.assertIn("MISSING: [[ghost]]", r.stdout)

    def test_abspath_detect_and_fix(self):
        p = "wiki/people/members/bob.md"
        fx.write(self.vault, p, "legacy: [[Workspaces/demo/vault/wiki/people/members/alice|Alice]]\n")
        self.assertEqual(check_links.check(self.vault, [p])[0][0], "ABSPATH")
        check_links.check(self.vault, [p], fix_abspath=True)
        with open(f"{self.vault}/{p}", encoding="utf-8") as fh:
            self.assertEqual(fh.read(), "legacy: [[alice|Alice]]\n")

    def test_clean_run_passes(self):
        fx.write(self.vault, "wiki/people/members/bob.md", "[[alice]]\n")
        r = fx.run("check_links.py", "--run-dir", self.run)
        self.assertEqual(r.returncode, 0, r.stdout)


if __name__ == "__main__":
    unittest.main()
