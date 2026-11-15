#!/usr/bin/env python3
"""Tests for build_portal_log.py — run with: python3 -m unittest test_build_portal_log.py -v"""

import os
import unittest

import _fixture as fx
import build_portal_log
import wikilib


class TestBuildPortalLog(unittest.TestCase):
    def setUp(self):
        self.vault, self.run = fx.make_vault(self)
        fx.init(self, self.vault, self.run)
        fx.plan_with(self.run, {"1-atomic": [
            fx.lane("members", ["wiki/people/members/"], creates=[("wiki/people/members", "bob")]),
            fx.lane("features", ["wiki/product/features/"], creates=[("wiki/product/features", "search")]),
        ]})
        wikilib.save_json(os.path.join(self.run, "manifests", "members.json"), {
            "lane": "members",
            "created": [{"path": "wiki/people/members/bob.md", "portal_section": "## People > ### Members", "hook": "new engineer"},
                        {"path": "wiki/people/members/alice.md", "portal_section": "## People > ### Members", "hook": "dup"}],
            "updated": [{"path": "wiki/people/members/alice.md", "what": "added team link"}],
            "gaps": ["team size 7 vs 8"]})
        wikilib.save_json(os.path.join(self.run, "manifests", "features.json"), {
            "lane": "features",
            "created": [{"path": "wiki/product/features/search.md", "portal_section": "## Product > ### Features", "hook": "search feature"}],
            "updated": []})

    def read(self, p):
        with open(os.path.join(self.vault, p), encoding="utf-8") as f:
            return f.read()

    def test_dry_run_changes_nothing(self):
        before = self.read("wiki/portal.md")
        _, entry = build_portal_log.build(self.run, "Demo ingest")
        self.assertEqual(self.read("wiki/portal.md"), before)
        self.assertIn("## [2026-02-02] ingest | Demo ingest", entry)
        self.assertIn("- members: [[bob]], [[alice]]", entry)
        self.assertIn("- team size 7 vs 8", entry)
        self.assertIn("`raw/notes/source.md`", entry)

    def test_apply_inserts_under_sections_idempotently(self):
        build_portal_log.build(self.run, "Demo ingest", apply=True)
        portal = self.read("wiki/portal.md")
        lines = portal.splitlines()
        self.assertEqual(lines[lines.index("- [[alice]] — existing member") + 1], "- [[bob]] — new engineer")
        self.assertEqual(portal.count("[[alice]]"), 1)  # existing entry not duplicated
        self.assertIn("## Product\n\n### Features\n- [[search]] — search feature", portal)
        self.assertIn("ingest | Demo ingest", self.read("wiki/log.md"))
        build_portal_log.build(self.run, "again", apply=True)
        self.assertEqual(self.read("wiki/portal.md").count("[[bob]]"), 1)

    def test_insert_missing_subsection_in_existing_top(self):
        lines = ["# P", "", "## People", "", "### Members", "- [[a]]", "", "## Sources", "- [[s]]"]
        out = build_portal_log.insert_portal(lines, "## People > ### Leaders", ["- [[l]]"])
        self.assertLess(out.index("### Leaders"), out.index("## Sources"))
        self.assertEqual(out[out.index("### Leaders") + 1], "- [[l]]")


if __name__ == "__main__":
    unittest.main()
