#!/usr/bin/env python3
"""
Unit tests for align-tables.py.
Covers the pure helpers plus format_table() and process_file().
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


at = _load("align_tables", "align-tables.py")


class TestDisplayWidth(unittest.TestCase):
	def test_ascii(self):
		self.assertEqual(at.display_width("abc"), 3)

	def test_empty(self):
		self.assertEqual(at.display_width(""), 0)

	def test_fullwidth_cjk_counts_two(self):
		self.assertEqual(at.display_width("你好"), 4)

	def test_mixed(self):
		self.assertEqual(at.display_width("a你"), 3)


class TestPad(unittest.TestCase):
	def test_left(self):
		self.assertEqual(at.pad("ab", 5, "left"), "ab   ")

	def test_right(self):
		self.assertEqual(at.pad("ab", 5, "right"), "   ab")

	def test_center(self):
		self.assertEqual(at.pad("ab", 5, "center"), " ab  ")

	def test_no_padding_when_already_wide(self):
		self.assertEqual(at.pad("abcde", 3, "left"), "abcde")

	def test_default_align_pads_right_side(self):
		self.assertEqual(at.pad("ab", 4, "none"), "ab  ")


class TestSplitRow(unittest.TestCase):
	def test_basic(self):
		self.assertEqual(at.split_row("| a | b |"), ["a", "b"])

	def test_without_outer_pipes(self):
		self.assertEqual(at.split_row("a | b"), ["a", "b"])

	def test_escaped_pipe_not_split(self):
		self.assertEqual(at.split_row("| [[x\\|y]] | b |"), ["[[x\\|y]]", "b"])

	def test_cells_are_trimmed(self):
		self.assertEqual(at.split_row("|  a  |   b|"), ["a", "b"])


class TestRowClassifiers(unittest.TestCase):
	def test_is_table_row_true(self):
		self.assertTrue(at.is_table_row("   | a |"))

	def test_is_table_row_false(self):
		self.assertFalse(at.is_table_row("plain text"))

	def test_is_separator_row_true(self):
		self.assertTrue(at.is_separator_row(["---", ":--", "--:", ":-:"]))

	def test_is_separator_row_false(self):
		self.assertFalse(at.is_separator_row(["a", "---"]))

	def test_is_separator_row_empty(self):
		self.assertFalse(at.is_separator_row([]))


class TestAlignmentsAndSeparator(unittest.TestCase):
	def test_alignments_from_separator(self):
		self.assertEqual(
			at.alignments_from_separator([":--", "--:", ":-:", "---"]),
			["left", "right", "center", "none"],
		)

	def test_separator_cell_variants(self):
		self.assertEqual(at.separator_cell(5, "none"), "-----")
		self.assertEqual(at.separator_cell(5, "left"), ":----")
		self.assertEqual(at.separator_cell(5, "right"), "----:")
		self.assertEqual(at.separator_cell(5, "center"), ":---:")


class TestFormatTable(unittest.TestCase):
	def test_columns_align_to_widest_cell(self):
		rows = [["Name", "Age"], ["---", "---"], ["Alice", "1"]]
		out = at.format_table(rows, sep_index=1)
		self.assertEqual(out[0], "| Name  | Age |")
		self.assertEqual(out[1], "| ----- | --- |")
		self.assertEqual(out[2], "| Alice | 1   |")

	def test_right_alignment_preserved(self):
		rows = [["N", "V"], ["---", "--:"], ["a", "10"]]
		out = at.format_table(rows, sep_index=1)
		# Right-aligned column pads on the left: "10" -> " 10" (width 3)
		self.assertEqual(out[2], "| a   |  10 |")
		self.assertEqual(out[1], "| --- | --: |")

	def test_ragged_rows_padded_to_max_cols(self):
		rows = [["a", "b", "c"], ["---", "---", "---"], ["x"]]
		out = at.format_table(rows, sep_index=1)
		self.assertEqual(out[2].count("|"), 4)


class TestProcessFile(unittest.TestCase):
	def _write(self, text):
		f = tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False)
		f.write(text)
		f.flush()
		f.close()
		return Path(f.name)

	def test_aligns_and_writes(self):
		path = self._write("| Name | Age |\n| --- | --- |\n| Alice | 1 |\n")
		try:
			blocks = at.process_file(path, dry_run=False)
			self.assertEqual(len(blocks), 1)
			self.assertIn("| Alice | 1   |", path.read_text())
		finally:
			path.unlink()

	def test_dry_run_does_not_write(self):
		path = self._write("| Name | Age |\n| --- | --- |\n| Alice | 1 |\n")
		try:
			original = path.read_text()
			blocks = at.process_file(path, dry_run=True)
			self.assertEqual(len(blocks), 1)
			self.assertEqual(path.read_text(), original)
		finally:
			path.unlink()

	def test_already_aligned_no_change(self):
		path = self._write("| Name  | Age |\n| ----- | --- |\n| Alice | 1   |\n")
		try:
			self.assertEqual(at.process_file(path, dry_run=False), [])
		finally:
			path.unlink()

	def test_block_without_separator_left_alone(self):
		path = self._write("| just | a | row |\n| and | another | one |\n")
		try:
			self.assertEqual(at.process_file(path, dry_run=False), [])
		finally:
			path.unlink()

	def test_non_table_content_preserved(self):
		path = self._write("# Heading\n\ntext\n\n| A | B |\n| --- | --- |\n| 1 | 2 |\n")
		try:
			at.process_file(path, dry_run=False)
			content = path.read_text()
			self.assertIn("# Heading", content)
			self.assertIn("text", content)
		finally:
			path.unlink()

	def test_reports_block_line_range(self):
		path = self._write("intro\n| A | B |\n| --- | --- |\n| 1 | 2 |\n")
		try:
			blocks = at.process_file(path, dry_run=True)
			self.assertEqual(blocks[0], (2, 4))
		finally:
			path.unlink()

	def test_missing_file_returns_empty(self):
		self.assertEqual(at.process_file(Path("/nonexistent/x.md")), [])


if __name__ == "__main__":
	unittest.main(verbosity=2)
