#!/usr/bin/env python3
"""
Unit tests for the unified normalize_markdown.py script.
Tests main() and process_file() with all three normalizers.
"""

import unittest
import tempfile
import sys
from pathlib import Path
from io import StringIO

from normalize_markdown import process_file


class TestProcessFileUnified(unittest.TestCase):
	"""Test process_file with different normalizer combinations"""

	def test_process_file_with_images_only(self):
		with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
			f.write("Done ![:done:](https://emoji.slack-edge.com/T123/done/abc.png)\n")
			f.flush()
			filepath = Path(f.name)

		try:
			from normalize_image_links import normalize_markdown_images
			normalizers = [normalize_markdown_images]
			changed, num_replacements = process_file(filepath, dry_run=False, normalizers=normalizers)
			self.assertTrue(changed)
			self.assertGreater(num_replacements, 0)

			content = filepath.read_text()
			self.assertIn("Done :done:", content)
		finally:
			filepath.unlink()

	def test_process_file_with_whitespace_only(self):
		with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
			f.write("```\nline1\n\nline2\n```\n")
			f.flush()
			filepath = Path(f.name)

		try:
			from normalize_whitespaces import normalize_whitespace_in_code_blocks
			normalizers = [normalize_whitespace_in_code_blocks]
			changed, num_replacements = process_file(filepath, dry_run=False, normalizers=normalizers)
			self.assertTrue(changed)

			content = filepath.read_text()
			self.assertIn("```\nline1\nline2\n```", content)
		finally:
			filepath.unlink()

	def test_process_file_with_all_normalizers(self):
		with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
			f.write("Emoji: ![:tada:](https://url/tada.png)  \n")
			f.write("```\ncode\n\nmore\n```\n")
			f.write("   \n")
			f.write("text\n")
			f.flush()
			filepath = Path(f.name)

		try:
			from normalize_image_links import normalize_markdown_images
			from normalize_whitespaces import normalize_whitespace, normalize_whitespace_in_code_blocks
			normalizers = [
				normalize_markdown_images,
				normalize_whitespace,
				normalize_whitespace_in_code_blocks,
			]
			changed, num_replacements = process_file(filepath, dry_run=False, normalizers=normalizers)
			self.assertTrue(changed)

			content = filepath.read_text()
			self.assertIn(":tada:", content)
			self.assertIn("```\ncode\nmore\n```", content)
		finally:
			filepath.unlink()

	def test_process_file_dry_run(self):
		with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
			f.write("Done ![:done:](https://emoji.slack-edge.com/T123/done/abc.png)\n")
			f.flush()
			filepath = Path(f.name)

		try:
			from normalize_image_links import normalize_markdown_images
			original_content = filepath.read_text()
			normalizers = [normalize_markdown_images]
			changed, num_replacements = process_file(filepath, dry_run=True, normalizers=normalizers)
			self.assertTrue(changed)

			# File should not be modified in dry run
			self.assertEqual(filepath.read_text(), original_content)
		finally:
			filepath.unlink()

	def test_process_file_no_changes(self):
		with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
			f.write("Just plain text\nNo changes needed\n")
			f.flush()
			filepath = Path(f.name)

		try:
			from normalize_image_links import normalize_markdown_images
			normalizers = [normalize_markdown_images]
			changed, num_replacements = process_file(filepath, dry_run=False, normalizers=normalizers)
			self.assertFalse(changed)
			self.assertEqual(num_replacements, 0)
		finally:
			filepath.unlink()

	def test_process_file_not_found(self):
		filepath = Path("/nonexistent/file.md")
		from normalize_image_links import normalize_markdown_images
		normalizers = [normalize_markdown_images]
		changed, num_replacements = process_file(filepath, dry_run=False, normalizers=normalizers)
		self.assertFalse(changed)

	def test_process_file_sequential_normalization(self):
		with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
			# File with both emoji and blank lines in code blocks
			f.write("Status: ![:done:](https://url/done.png)\n")
			f.write("```\ncode\n\n\nmore\n```\n")
			f.write("\n\n\n")
			f.write("End\n")
			f.flush()
			filepath = Path(f.name)

		try:
			from normalize_image_links import normalize_markdown_images
			from normalize_whitespaces import normalize_whitespace, normalize_whitespace_in_code_blocks
			# Apply in sequence: images -> whitespace -> code blocks
			normalizers = [
				normalize_markdown_images,
				normalize_whitespace,
				normalize_whitespace_in_code_blocks,
			]
			changed, num_replacements = process_file(filepath, dry_run=False, normalizers=normalizers)
			self.assertTrue(changed)

			content = filepath.read_text()
			# All transformations should be applied
			self.assertIn(":done:", content)
			self.assertIn("```\ncode\nmore\n```", content)
		finally:
			filepath.unlink()

	def test_process_file_empty_normalizers_list(self):
		with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
			f.write("Done ![:done:](https://emoji.slack-edge.com/T123/done/abc.png)\n")
			f.flush()
			filepath = Path(f.name)

		try:
			original_content = filepath.read_text()
			changed, num_replacements = process_file(filepath, dry_run=False, normalizers=[])
			self.assertFalse(changed)
			self.assertEqual(filepath.read_text(), original_content)
		finally:
			filepath.unlink()

	def test_process_file_multiple_image_types(self):
		with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
			f.write("Emoji: ![:tada:](https://url/a.png)\n")
			f.write("Zoom: ![Speaker 1](https://us01cnst1.zoom.com/img.png)\n")
			f.write("Base64: ![alt](data:image/png;base64,abc)\n")
			f.flush()
			filepath = Path(f.name)

		try:
			from normalize_image_links import normalize_markdown_images
			normalizers = [normalize_markdown_images]
			changed, num_replacements = process_file(filepath, dry_run=False, normalizers=normalizers)
			self.assertTrue(changed)
			self.assertEqual(num_replacements, 3)
		finally:
			filepath.unlink()


if __name__ == "__main__":
	unittest.main(verbosity=2)
