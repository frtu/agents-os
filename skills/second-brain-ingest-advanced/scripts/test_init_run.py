#!/usr/bin/env python3
"""Tests for init_run.py — run with: python3 -m unittest test_init_run.py -v"""

import os
import unittest

import _fixture as fx
import init_run
import wikilib


class TestInitRun(unittest.TestCase):
    def test_creates_run_files(self):
        vault, run = fx.make_vault(self)
        fx.init(self, vault, run)
        for f in ("baseline.json", "inventory.json", "sources.json", "plan.json"):
            self.assertTrue(os.path.exists(os.path.join(run, f)), f)
        base = wikilib.load_json(os.path.join(run, "baseline.json"))
        self.assertIn("wiki/people/members/alice.md", base["files"])
        inv = wikilib.load_json(os.path.join(run, "inventory.json"))
        self.assertEqual(inv["slugs"]["people/members"], ["alice"])
        self.assertIn("### Members", inv["portal_headers"])
        src = wikilib.load_json(os.path.join(run, "sources.json"))
        self.assertEqual(src[0]["lines"], 2)
        plan = wikilib.load_json(os.path.join(run, "plan.json"))
        self.assertEqual([p["id"] for p in plan["phases"]], ["1-atomic", "2-bubble-up", "3-deliverable"])
        self.assertEqual(plan["trigger"], "test ingest")

    def test_keeps_existing_plan(self):
        vault, run = fx.make_vault(self)
        fx.init(self, vault, run)
        fx.plan_with(run, {}, target="kept")
        fx.init(self, vault, run)
        self.assertEqual(wikilib.load_json(os.path.join(run, "plan.json"))["target_system"], "kept")

    def test_missing_source_fails(self):
        vault, run = fx.make_vault(self)
        r = fx.run("init_run.py", "--vault", vault, "--run-dir", run, "--trigger", "t", "--source", "raw/nope.md")
        self.assertEqual(r.returncode, 1)
        self.assertIn("MISSING SOURCE", r.stderr)

    def test_normalise_pdf_text_rejoins_words(self):
        self.assertEqual(init_run.normalise_pdf_text("Led\n \n3\n \nteams"), "Led 3 teams\n")


if __name__ == "__main__":
    unittest.main()
