#!/usr/bin/env python3
"""Tests for replace_from_dictionary.py (fixture dictionary, no real entries).

Run: python3 -m unittest test_replace_from_dictionary   (from this directory)
"""

import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import replace_from_dictionary as rfd  # noqa: E402

FIXTURE = {
    "version": 2,
    "known_noise": [],
    "corrections": [
        {"correct": "Flink", "variants": ["Flinc", "Fleenk"], "ambiguous_variants": ["Flint"], "wikilink": ""},
        {"correct": "Kafka", "variants": ["Kafca"], "ambiguous_variants": [], "wikilink": "[[kafka|Kafka]]"},
    ],
}

# Hyphen-joined tokens are not whole words (owned rule in normalise_transcript.py): Fleenk-style stays.
TEXT = "We moved to flinc last week. Fleenk-style jobs? No: Fleenkish stays.\nKafca and Flint here. See [[Kafca]].\n"
EXPECTED = "We moved to Flink last week. Fleenk-style jobs? No: Fleenkish stays.\nKafka and Flint here. See [[Kafca]].\n"


class ReplaceFromDictionaryTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.cfg = self.root / "corrections.json"
        self.cfg.write_text(json.dumps(FIXTURE), encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def run_cli(self, *args, stdin=None):
        out, err = io.StringIO(), io.StringIO()
        old_stdin = sys.stdin
        if stdin is not None:
            sys.stdin = io.StringIO(stdin)
        try:
            with redirect_stdout(out), redirect_stderr(err):
                code = rfd.main([*args, "--corrections", str(self.cfg)])
        finally:
            sys.stdin = old_stdin
        return code, out.getvalue(), err.getvalue()

    def write(self, rel, text=TEXT):
        p = self.root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
        return p

    def test_dry_run_reports_and_writes_nothing(self):
        f = self.write("notes/t.md")
        code, out, _ = self.run_cli(str(f))
        self.assertEqual(code, 0)
        self.assertEqual(f.read_text(encoding="utf-8"), TEXT)
        self.assertIn("2 replacement(s), 1 ambiguous", out)
        self.assertIn("dry run", out)

    def test_write_in_place_skips_wikilinks_and_ambiguous(self):
        f = self.write("notes/t.md")
        code, _, _ = self.run_cli(str(f), "--write")
        self.assertEqual(code, 0)
        self.assertEqual(f.read_text(encoding="utf-8"), EXPECTED)

    def test_write_refused_inside_raw(self):
        f = self.write("raw/t.md")
        code, _, err = self.run_cli(str(f), "--write")
        self.assertEqual(code, 2)
        self.assertIn("refusing --write inside raw/", err)
        self.assertEqual(f.read_text(encoding="utf-8"), TEXT)

    def test_out_dir_mirrors_tree_and_keeps_raw_untouched(self):
        src = self.root / "raw"
        a = self.write("raw/a.md")
        self.write("raw/sub/b.md")
        self.write("raw/ignored.txt", "Kafca")
        out_dir = self.root / "clean"
        code, out, _ = self.run_cli(str(src), "--out-dir", str(out_dir))
        self.assertEqual(code, 0)
        self.assertEqual(a.read_text(encoding="utf-8"), TEXT)
        self.assertEqual((out_dir / "a.md").read_text(encoding="utf-8"), EXPECTED)
        self.assertEqual((out_dir / "sub" / "b.md").read_text(encoding="utf-8"), EXPECTED)
        self.assertFalse((out_dir / "ignored.txt").exists())
        self.assertIn("2 file(s), 2 changed", out)

    def test_stdin_filter(self):
        code, out, err = self.run_cli("-", stdin=TEXT)
        self.assertEqual(code, 0)
        self.assertEqual(out, EXPECTED)
        self.assertIn("2 replacement(s), 1 ambiguous left", err)

    def test_list_ambiguous(self):
        f = self.write("notes/t.md")
        _, out, _ = self.run_cli(str(f), "--list-ambiguous")
        self.assertIn("L2: 'Flint' (maybe Flink)", out)

    def test_missing_path_is_usage_error(self):
        code, _, err = self.run_cli(str(self.root / "nope.md"))
        self.assertEqual(code, 2)
        self.assertIn("not found", err)


if __name__ == "__main__":
    unittest.main()
