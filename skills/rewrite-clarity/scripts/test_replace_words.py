#!/usr/bin/env python3
"""Tests for replace_words.py.

Run: python3 -m unittest test_replace_words   (from this directory)
"""

import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import replace_words as rw  # noqa: E402

FIXTURE = {
    "version": 1,
    "replacements": [
        {"verbose": "in order to", "direct": "to"},
        {"verbose": "prior to", "direct": "before"},
        {"verbose": "due to the fact that", "direct": "because"},
        {"verbose": "the fact", "direct": "SHOULD-NOT-FIRE-INSIDE-LONGER"},
    ],
    "suggestions": [{"verbose": "for the purpose of", "direct": "to"}],
    "keep": [],
}


class ApplyTest(unittest.TestCase):
    def run_apply(self, text, cfg=FIXTURE):
        return rw.apply(text, cfg)

    def test_case_is_preserved(self):
        new, applied, _ = self.run_apply("In order to ship. IN ORDER TO win. We act in order to learn.")
        self.assertEqual(new, "To ship. TO win. We act to learn.")
        self.assertEqual(len(applied), 3)

    def test_longest_phrase_wins_and_no_chaining(self):
        new, applied, _ = self.run_apply("We stopped due to the fact that it broke.")
        self.assertEqual(new, "We stopped because it broke.")
        self.assertEqual([a[1] for a in applied], ["due to the fact that"])

    def test_whole_words_only(self):
        new, applied, _ = self.run_apply("The priority to-do list; apriori to.")
        self.assertEqual(applied, [])
        self.assertEqual(new, "The priority to-do list; apriori to.")

    def test_phrase_across_line_break_and_line_numbers(self):
        text = "line one\nwe act in order\nto learn\nprior to launch\n"
        new, applied, _ = self.run_apply(text)
        self.assertEqual(new, "line one\nwe act to learn\nbefore launch\n")
        self.assertEqual([a[0] for a in applied], [2, 4])

    def test_protected_spans_untouched(self):
        text = (
            "Use `in order to` here.\n"
            "```\nin order to\n```\n"
            "See [[in order to]] and [link](https://x.io/in-order-to) https://x.io/prior to\n"
            "Real: in order to go.\n"
        )
        new, applied, _ = self.run_apply(text)
        self.assertEqual(len(applied), 1)
        self.assertEqual(applied[0][0], 6)
        self.assertIn("Real: to go.", new)
        self.assertIn("`in order to`", new)
        self.assertIn("[[in order to]]", new)

    def test_suggestions_reported_never_applied(self):
        text = "Built for the purpose of testing.\n"
        new, applied, suggested = self.run_apply(text)
        self.assertEqual(new, text)
        self.assertEqual(applied, [])
        self.assertEqual(suggested, [(1, "for the purpose of", "to")])

    def test_empty_tiers(self):
        new, applied, suggested = self.run_apply("in order to", {"replacements": [], "suggestions": []})
        self.assertEqual((new, applied, suggested), ("in order to", [], []))


class CliTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.cfg = self.root / "dict.json"
        self.cfg.write_text(json.dumps(FIXTURE), encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def cli(self, *args, stdin=None):
        out, err = io.StringIO(), io.StringIO()
        old = sys.stdin
        if stdin is not None:
            sys.stdin = io.StringIO(stdin)
        try:
            with redirect_stdout(out), redirect_stderr(err):
                code = rw.main([*args, "--config", str(self.cfg)])
        finally:
            sys.stdin = old
        return code, out.getvalue(), err.getvalue()

    def test_dry_run_then_write(self):
        f = self.root / "d" / "doc.md"
        f.parent.mkdir()
        f.write_text("Prior to launch, for the purpose of QA.\n", encoding="utf-8")
        code, out, _ = self.cli(str(self.root / "d"))
        self.assertEqual(code, 0)
        self.assertIn("1 replaced, 1 to review", out)
        self.assertEqual(f.read_text(encoding="utf-8"), "Prior to launch, for the purpose of QA.\n")
        self.cli(str(f), "--write")
        self.assertEqual(f.read_text(encoding="utf-8"), "Before launch, for the purpose of QA.\n")

    def test_stdin_filter(self):
        code, out, err = self.cli("-", stdin="in order to win")
        self.assertEqual((code, out), (0, "to win"))
        self.assertIn("1 replaced, 0 to review", err)

    def test_missing_path(self):
        code, _, err = self.cli(str(self.root / "nope.md"))
        self.assertEqual(code, 2)
        self.assertIn("not found", err)

    def test_shipped_dictionary_is_valid(self):
        cfg = rw.load(rw.DEFAULT_CFG)
        for tier in ("replacements", "suggestions"):
            for e in cfg[tier]:
                self.assertEqual(e["verbose"], e["verbose"].lower(), e)
                self.assertTrue(e["direct"], e)
        verbose = [e["verbose"] for t in ("replacements", "suggestions") for e in cfg[t]]
        self.assertEqual(len(verbose), len(set(verbose)), "duplicate verbose phrase across tiers")


if __name__ == "__main__":
    unittest.main()
