#!/usr/bin/env python3
"""Tests for check_scope.py — run with: python3 -m unittest test_check_scope.py -v"""

import os
import unittest

import _fixture as fx
import check_scope
import wikilib


class TestCheckScope(unittest.TestCase):
    def setUp(self):
        self.vault, self.run = fx.make_vault(self)
        fx.init(self, self.vault, self.run)
        fx.plan_with(self.run, {"1-atomic": [
            fx.lane("members", ["wiki/people/members/"], creates=[("wiki/people/members", "bob")]),
        ]})

    def manifest(self, lane="members", data=None):
        wikilib.save_json(os.path.join(self.run, "manifests", f"{lane}.json"),
                          data if data is not None else {"lane": lane, "created": [], "updated": []})

    def test_clean_phase(self):
        fx.write(self.vault, "wiki/people/members/bob.md", "# Bob\n")
        self.manifest()
        self.assertEqual(check_scope.check(self.run, "1-atomic")[0], [])

    def test_violations(self):
        fx.write(self.vault, "wiki/concepts/patterns/stray.md", "x\n")
        fx.write(self.vault, "wiki/portal.md", "# changed\n")
        errors, _ = check_scope.check(self.run, "1-atomic")
        joined = "\n".join(errors)
        self.assertIn("OUT_OF_SCOPE: wiki/concepts/patterns/stray.md", joined)
        self.assertIn("OWNED_TOUCHED: wiki/portal.md", joined)
        self.assertIn("NOT_CREATED: wiki/people/members/bob.md", joined)
        self.assertIn("NO_MANIFEST: members", joined)
        errors, _ = check_scope.check(self.run, "1-atomic", orchestrator_done=True)
        self.assertNotIn("OWNED_TOUCHED", "\n".join(errors))

    def test_bad_manifest(self):
        fx.write(self.vault, "wiki/people/members/bob.md", "# Bob\n")
        self.manifest(data={"lane": "members", "created": "oops"})
        errors, _ = check_scope.check(self.run, "1-atomic")
        self.assertTrue(any(e.startswith("BAD_MANIFEST") for e in errors), errors)


if __name__ == "__main__":
    unittest.main()
