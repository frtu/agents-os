#!/usr/bin/env python3
"""Tests for changed_files.py — run with: python3 -m unittest test_changed_files.py -v"""

import json
import os
import unittest

import _fixture as fx
import changed_files
import wikilib


class TestChangedFiles(unittest.TestCase):
    def test_created_updated_deleted(self):
        vault, run = fx.make_vault(self)
        fx.init(self, vault, run)
        fx.write(vault, "wiki/people/members/bob.md", "# Bob\n")
        fx.write(vault, "wiki/people/members/alice.md", "# Alice\nmore\n")
        os.remove(os.path.join(vault, "wiki/concepts/patterns/old-pattern.md"))
        fx.write(vault, "output/review.md", "# Review\n")
        d = changed_files.diff(run)
        self.assertEqual(d["created"], ["output/review.md", "wiki/people/members/bob.md"])
        self.assertEqual(d["updated"], ["wiki/people/members/alice.md"])
        self.assertEqual(d["deleted"], ["wiki/concepts/patterns/old-pattern.md"])

    def test_touch_without_change_is_not_updated(self):
        vault, run = fx.make_vault(self)
        fx.init(self, vault, run)
        fx.write(vault, "wiki/people/members/alice.md", "# Alice\n")  # same content
        self.assertEqual(changed_files.diff(run)["updated"], [])

    def test_pre_dirty_overlap_and_formats(self):
        vault, run = fx.make_vault(self)
        fx.init(self, vault, run)
        base = wikilib.load_json(os.path.join(run, "baseline.json"))
        base["git_dirty"] = ["wiki/people/members/alice.md"]
        wikilib.save_json(os.path.join(run, "baseline.json"), base)
        fx.write(vault, "wiki/people/members/alice.md", "changed\n")
        self.assertEqual(changed_files.diff(run)["pre_dirty_overlap"], ["wiki/people/members/alice.md"])
        r = fx.run("changed_files.py", "--run-dir", run, "--format", "9log")
        self.assertIn("Updated: alice.md", r.stdout)
        r = fx.run("changed_files.py", "--run-dir", run, "--format", "lines")
        self.assertEqual(r.stdout.strip(), "wiki/people/members/alice.md")
        r = fx.run("changed_files.py", "--run-dir", run)
        self.assertEqual(json.loads(r.stdout)["updated"], ["wiki/people/members/alice.md"])


if __name__ == "__main__":
    unittest.main()
