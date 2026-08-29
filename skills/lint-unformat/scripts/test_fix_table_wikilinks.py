#!/usr/bin/env python3
"""
Unit tests for fix-table-wikilinks.py.
Tests fix_wikilinks_in_line() and process_file().
"""

import importlib.util
import tempfile
import unittest
from pathlib import Path


def _load(name, filename):
	spec = importlib.util.spec_from_file_location(name, Path(__file__).parent / filename)
	mod = importlib.util.module_from_spec(spec)
	spec.loader.exec_module(mod)
	return mod


ftw = _load("fix_table_wikilinks", "fix-table-wikilinks.py")


class TestFixWikilinksInLine(unittest.TestCase):
	def test_escapes_unescaped_pipe(self):
		self.assertEqual(
			ftw.fix_wikilinks_in_line("| [[link|name]] |"),
			"| [[link\\|name]] |",
		)

	def test_leaves_already_escaped(self):
		line = "| [[link\\|name]] |"
		self.assertEqual(ftw.fix_wikilinks_in_line(line), line)

	def test_wikilink_without_pipe_unchanged(self):
		line = "| [[link]] | text |"
		self.assertEqual(ftw.fix_wikilinks_in_line(line), line)

	def test_multiple_wikilinks_in_line(self):
		self.assertEqual(
			ftw.fix_wikilinks_in_line("| [[a|A]] | [[b|B]] |"),
			"| [[a\\|A]] | [[b\\|B]] |",
		)

	def test_plain_pipe_not_in_wikilink_unchanged(self):
		line = "| a | b | c |"
		self.assertEqual(ftw.fix_wikilinks_in_line(line), line)


class TestProcessFile(unittest.TestCase):
	def _write(self, text):
		f = tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False)
		f.write(text)
		f.flush()
		f.close()
		return Path(f.name)

	def test_fixes_table_row_and_writes(self):
		path = self._write("| [[link|name]] | x |\n")
		try:
			changes = ftw.process_file(path, dry_run=False)
			self.assertEqual(len(changes), 1)
			self.assertIn("[[link\\|name]]", path.read_text())
		finally:
			path.unlink()

	def test_dry_run_does_not_write(self):
		path = self._write("| [[link|name]] | x |\n")
		try:
			original = path.read_text()
			changes = ftw.process_file(path, dry_run=True)
			self.assertEqual(len(changes), 1)
			self.assertEqual(path.read_text(), original)
		finally:
			path.unlink()

	def test_non_table_line_not_touched(self):
		path = self._write("Some prose with [[link|name]] inline.\n")
		try:
			changes = ftw.process_file(path, dry_run=False)
			self.assertEqual(changes, [])
			self.assertIn("[[link|name]]", path.read_text())
		finally:
			path.unlink()

	def test_no_wikilinks_no_changes(self):
		path = self._write("| a | b |\n| c | d |\n")
		try:
			self.assertEqual(ftw.process_file(path, dry_run=False), [])
		finally:
			path.unlink()

	def test_reports_correct_line_number(self):
		path = self._write("intro\n\n| [[a|A]] | b |\n")
		try:
			changes = ftw.process_file(path, dry_run=True)
			self.assertEqual(changes[0][0], 3)
		finally:
			path.unlink()

	def test_missing_file_returns_empty(self):
		self.assertEqual(ftw.process_file(Path("/nonexistent/x.md")), [])


if __name__ == "__main__":
	unittest.main(verbosity=2)
