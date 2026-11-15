#!/usr/bin/env python3
"""Tests for validate_plan.py — run with: python3 -m unittest test_validate_plan.py -v"""

import os
import unittest

import _fixture as fx
import validate_plan
import wikilib

TEMPLATES = os.path.join(fx.HERE, "..", "references", "templates")


class TestValidatePlan(unittest.TestCase):
    def setUp(self):
        self.vault, self.run = fx.make_vault(self)
        fx.init(self, self.vault, self.run)

    def errors(self, lanes_by_phase):
        plan = fx.plan_with(self.run, lanes_by_phase)
        inv = wikilib.load_json(os.path.join(self.run, "inventory.json"))
        return validate_plan.validate(plan, inv, TEMPLATES)[0]

    def test_valid_plan(self):
        e = self.errors({"1-atomic": [
            fx.lane("members", ["wiki/people/members/"], creates=[("wiki/people/members", "bob")]),
            fx.lane("patterns", ["wiki/concepts/patterns/"], creates=[("wiki/concepts/patterns", "new-one")],
                    updates=["wiki/concepts/patterns/old-pattern.md"]),
        ]})
        self.assertEqual(e, [])
        r = fx.run("validate_plan.py", "--run-dir", self.run, "--templates", TEMPLATES)
        self.assertEqual(r.returncode, 0, r.stdout)

    def test_update_target_must_exist(self):
        e = self.errors({"1-atomic": [fx.lane("a", ["wiki/people/members/"], updates=["wiki/people/members/ghost.md"])]})
        self.assertTrue(any("does not exist" in x for x in e), e)

    def test_overlapping_parallel_scopes(self):
        e = self.errors({"1-atomic": [
            fx.lane("a", ["wiki/people/"], creates=[("wiki/people/members", "bob")]),
            fx.lane("b", ["wiki/people/members/carol.md"], creates=[("wiki/people/members", "carol")]),
        ]})
        self.assertTrue(any("overlapping" in x for x in e), e)

    def test_existing_slug_must_be_update(self):
        e = self.errors({"1-atomic": [fx.lane("a", ["wiki/people/members/"], creates=[("wiki/people/members", "alice")])]})
        self.assertTrue(any("already exists" in x for x in e), e)

    def test_duplicate_slug_across_phases(self):
        e = self.errors({
            "1-atomic": [fx.lane("a", ["wiki/people/members/"], creates=[("wiki/people/members", "bob")])],
            "2-bubble-up": [fx.lane("b", ["wiki/synthesis/"], creates=[("wiki/synthesis", "bob")], template="brief-bubble-up")],
        })
        self.assertTrue(any("also created" in x for x in e), e)

    def test_scope_and_owned_and_slug_format(self):
        e = self.errors({"1-atomic": [
            fx.lane("a", ["wiki/"], creates=[("wiki/x", "Bad_Slug")]),
            fx.lane("b", ["wiki/sources/"], creates=[("wiki/people", "zed")], template="nope"),
        ]})
        joined = "\n".join(e)
        self.assertIn("orchestrator-owned", joined)
        self.assertIn("kebab-case", joined)
        self.assertIn("outside write_scope", joined)
        self.assertIn("template 'nope' not found", joined)


if __name__ == "__main__":
    unittest.main()
