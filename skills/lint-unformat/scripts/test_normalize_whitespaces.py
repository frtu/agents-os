#!/usr/bin/env python3
"""
Unit tests for normalize_whitespace and normalize_whitespace_in_code_blocks functions
in normalize_whitespaces.py
"""

import unittest
from normalize_whitespaces import (
	normalize_whitespace,
	normalize_whitespace_in_code_blocks,
)


class TestNormalizeWhitespace(unittest.TestCase):
	"""Test normalize_whitespace function"""

	def test_removes_trailing_spaces_on_blank_lines(self):
		input_text = "line1\n    \nline2\n"
		expected = "line1\n\nline2\n"
		self.assertEqual(normalize_whitespace(input_text), expected)

	def test_preserves_trailing_double_space(self):
		input_text = "line1  \nline2\n"
		expected = "line1  \nline2\n"
		self.assertEqual(normalize_whitespace(input_text), expected)

	def test_collapses_multiple_blank_lines(self):
		input_text = "line1\n\n\n\nline2\n"
		expected = "line1\n\nline2\n"
		self.assertEqual(normalize_whitespace(input_text), expected)

	def test_ensures_single_trailing_newline(self):
		input_text = "line1\nline2"
		expected = "line1\nline2\n"
		self.assertEqual(normalize_whitespace(input_text), expected)

	def test_removes_extra_trailing_newlines(self):
		input_text = "line1\nline2\n\n\n"
		# Collapses multiple blank lines to single, then adds final newline
		expected = "line1\nline2\n\n"
		self.assertEqual(normalize_whitespace(input_text), expected)

	def test_mixed_whitespace_scenarios(self):
		input_text = "line1  \n  \nline2\n\n\nline3"
		expected = "line1  \n\nline2\n\nline3\n"
		self.assertEqual(normalize_whitespace(input_text), expected)

	def test_empty_string(self):
		self.assertEqual(normalize_whitespace(""), "\n")

	def test_single_line_no_trailing_newline(self):
		input_text = "single line"
		expected = "single line\n"
		self.assertEqual(normalize_whitespace(input_text), expected)

	def test_only_whitespace(self):
		input_text = "   \n\n   \n"
		expected = "\n"
		self.assertEqual(normalize_whitespace(input_text), expected)

	def test_preserves_content_with_internal_spaces(self):
		input_text = "text with  spaces  here\nmore text\n"
		expected = "text with  spaces  here\nmore text\n"
		self.assertEqual(normalize_whitespace(input_text), expected)

	def test_removes_blank_lines_after_headers(self):
		input_text = "# Header\n\n- list item\n"
		expected = "# Header\n- list item\n"
		self.assertEqual(normalize_whitespace(input_text), expected)

	def test_removes_blank_lines_before_list_items(self):
		input_text = "paragraph\n\n- list item\n"
		# Blank lines before list items are removed
		expected = "paragraph\n- list item\n"
		self.assertEqual(normalize_whitespace(input_text), expected)


class TestNormalizeWhitespaceInCodeBlocks(unittest.TestCase):
	"""Test normalize_whitespace_in_code_blocks function"""

	def test_removes_blank_lines_in_code_block(self):
		input_text = "```\nline1\n\nline2\n```\n"
		expected = "```\nline1\nline2\n```\n"
		self.assertEqual(normalize_whitespace_in_code_blocks(input_text), expected)

	def test_preserves_blank_lines_outside_code_blocks(self):
		input_text = "text\n\n\nmore text\n```\ncode\n```\n"
		expected = "text\n\n\nmore text\n```\ncode\n```\n"
		self.assertEqual(normalize_whitespace_in_code_blocks(input_text), expected)

	def test_multiple_code_blocks(self):
		input_text = "```\na\n\nb\n```\ntext\n```\nc\n\nd\n```\n"
		expected = "```\na\nb\n```\ntext\n```\nc\nd\n```\n"
		self.assertEqual(normalize_whitespace_in_code_blocks(input_text), expected)

	def test_nested_triple_backticks(self):
		input_text = "```\ncode\n```\ntext\n```\nmore\n```\n"
		expected = "```\ncode\n```\ntext\n```\nmore\n```\n"
		self.assertEqual(normalize_whitespace_in_code_blocks(input_text), expected)

	def test_code_block_with_only_blank_lines(self):
		input_text = "```\n\n\n```\n"
		expected = "```\n```\n"
		self.assertEqual(normalize_whitespace_in_code_blocks(input_text), expected)

	def test_no_code_blocks(self):
		input_text = "just regular text\nwith some lines\n"
		expected = "just regular text\nwith some lines\n"
		self.assertEqual(normalize_whitespace_in_code_blocks(input_text), expected)

	def test_code_block_with_indented_content(self):
		input_text = "```\n  indented\n\n  more indented\n```\n"
		expected = "```\n  indented\n  more indented\n```\n"
		self.assertEqual(normalize_whitespace_in_code_blocks(input_text), expected)

	def test_code_block_with_whitespace_lines(self):
		input_text = "```\nline1\n   \nline2\n```\n"
		expected = "```\nline1\nline2\n```\n"
		self.assertEqual(normalize_whitespace_in_code_blocks(input_text), expected)

	def test_unclosed_code_block(self):
		input_text = "```\nline1\n\nline2\n"
		# Should treat everything after opening ``` as in code block
		expected = "```\nline1\nline2\n"
		self.assertEqual(normalize_whitespace_in_code_blocks(input_text), expected)

	def test_code_block_with_inline_backticks(self):
		input_text = "```\ncode with `backticks`\n\nmore code\n```\n"
		expected = "```\ncode with `backticks`\nmore code\n```\n"
		self.assertEqual(normalize_whitespace_in_code_blocks(input_text), expected)

	def test_empty_code_block(self):
		input_text = "```\n```\n"
		expected = "```\n```\n"
		self.assertEqual(normalize_whitespace_in_code_blocks(input_text), expected)


class TestIntegrationWhitespace(unittest.TestCase):
	"""Integration tests for whitespace functions"""

	def test_normalize_then_code_blocks(self):
		input_text = "```\nline1\n  \nline2  \n\n\nline3\n```\ntext"
		# First normalize whitespace
		after_whitespace = normalize_whitespace(input_text)
		# Then remove blank lines in code blocks
		result = normalize_whitespace_in_code_blocks(after_whitespace)
		# Should have removed blank lines from code block
		self.assertIn("```\nline1\nline2", result)

	def test_combined_complex_document(self):
		input_text = (
			"# Header  \n"
			"\n"
			"Paragraph with trailing spaces  \n"
			"```\ncode\n\n\nmore code\n```\n"
			"\n\n"
			"Another paragraph\n"
		)
		# Apply both transformations
		after_first = normalize_whitespace(input_text)
		after_second = normalize_whitespace_in_code_blocks(after_first)
		# Verify transformations
		self.assertIn("# Header  \n", after_second)  # Header preserved
		self.assertIn("```\ncode\nmore code\n```", after_second)  # Code block cleaned


if __name__ == "__main__":
	unittest.main(verbosity=2)
