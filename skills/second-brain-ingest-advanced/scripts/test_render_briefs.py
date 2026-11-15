#!/usr/bin/env python3
"""Tests for render_briefs.py — run with: python3 -m unittest test_render_briefs.py -v"""

import os
import unittest

import _fixture as fx

TEMPLATES = os.path.join(fx.HERE, "..", "references", "templates")


class TestRenderBriefs(unittest.TestCase):
    def test_renders_all_placeholders(self):
        vault, run = fx.make_vault(self)
        fx.init(self, vault, run)
        fx.plan_with(run, {"1-atomic": [
            fx.lane("members", ["wiki/people/members/"], creates=[("wiki/people/members", "bob")]),
            fx.lane("patterns", ["wiki/concepts/patterns/"], creates=[("wiki/concepts/patterns", "new-one")]),
        ]})
        r = fx.run("render_briefs.py", "--run-dir", run, "--phase", "1-atomic", "--templates", TEMPLATES)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("launch them in parallel", r.stdout)
        with open(os.path.join(run, "briefs", "1-atomic--members.md"), encoding="utf-8") as f:
            text = f.read()
        self.assertNotIn("{{", text)
        self.assertIn("wiki/people/members/bob.md", text)          # CREATES
        self.assertIn("[[new-one]]", text)                         # SIBLING_SLUGS
        self.assertIn("wiki/concepts/patterns/", text)             # FORBIDDEN (other lane scope)
        self.assertIn("wiki/portal.md", text)                      # FORBIDDEN (owned)
        self.assertIn(os.path.join("manifests", "members.json"), text)

    def test_every_template_has_no_unknown_placeholder(self):
        import re
        import render_briefs
        plan = {"vault": "/v", "phases": [{"id": "p", "lanes": [{"id": "l"}]}]}
        allowed = set(render_briefs.render(plan, "p", {"id": "l"}, [], "/r"))
        for name in os.listdir(TEMPLATES):
            if name.startswith("brief-"):
                with open(os.path.join(TEMPLATES, name), encoding="utf-8") as f:
                    used = set(re.findall(r"\{\{([A-Z_]+)\}\}", f.read()))
                self.assertTrue(used <= allowed, f"{name}: {used - allowed}")


if __name__ == "__main__":
    unittest.main()
