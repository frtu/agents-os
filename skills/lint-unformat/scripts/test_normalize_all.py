#!/usr/bin/env python3
"""
Comprehensive unit tests for lint-unformat scripts.
Tests all functions in normalize_image_links.py and normalize_whitespaces.py
"""

import unittest
import tempfile
from pathlib import Path

from normalize_image_links import (
    normalize_markdown_images,
    process_file as process_slack_emoji_file,
)
from normalize_whitespaces import (
    normalize_whitespace,
    normalize_whitespace_in_code_blocks,
    process_file as process_blank_lines_file,
)


class TestNormalizeWhitespace(unittest.TestCase):
    """Test normalize_whitespace from normalize_whitespaces.py"""

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


class TestRemoveBlankLinesInCodeBlocks(unittest.TestCase):
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


class TestNormalizeMarkdownImages(unittest.TestCase):
    """Test normalize_markdown_images function"""

    def test_simple_slack_emoji(self):
        input_text = "![:tada:](https://emoji.slack-edge.com/T086B9BTPEJ/tada/abc.png)"
        expected = ":tada:"
        self.assertEqual(normalize_markdown_images(input_text), expected)

    def test_animated_emoji(self):
        input_text = "![:tada-animated:](https://emoji.slack-edge.com/T086B9BTPEJ/tada-animated/3743b73b31c22c82.gif)"
        expected = ":tada-animated:"
        self.assertEqual(normalize_markdown_images(input_text), expected)

    def test_bracketed_emoji(self):
        input_text = "[![:done:](https://emoji.slack-edge.com/T086B9BTPEJ/done/c11bf3db1f90897f.jpg)]"
        expected = "[:done:]"
        self.assertEqual(normalize_markdown_images(input_text), expected)

    def test_zoom_speaker_image(self):
        input_text = "![Speaker 1](https://us01cnst1.zoom.com/fe-static/recording-player/img/zr_default.b8180c09.png)"
        expected = "Speaker 1"
        self.assertEqual(normalize_markdown_images(input_text), expected)

    def test_base64_image(self):
        input_text = "![alt](data:image/png;base64,iVBORw0KGgo...)"
        expected = "alt"
        self.assertEqual(normalize_markdown_images(input_text), expected)

    def test_multiple_emoji_same_line(self):
        input_text = "![:thumbsup:](https://url/a.png) ![:thumbsdown:](https://url/b.png)"
        expected = ":thumbsup: :thumbsdown:"
        self.assertEqual(normalize_markdown_images(input_text), expected)

    def test_emoji_with_surrounding_text(self):
        input_text = "Hello ![:wave:](https://emoji.slack-edge.com/T123/wave/abc.png) world"
        expected = "Hello :wave: world"
        self.assertEqual(normalize_markdown_images(input_text), expected)

    def test_preserves_regular_markdown_images(self):
        input_text = "![alt text](https://example.com/image.png)"
        self.assertEqual(normalize_markdown_images(input_text), input_text)

    def test_preserves_other_markdown(self):
        input_text = "**bold** and _italic_ with ![:emoji:](https://url/a.png)"
        expected = "**bold** and _italic_ with :emoji:"
        self.assertEqual(normalize_markdown_images(input_text), expected)

    def test_emoji_at_line_boundaries(self):
        input_text = "![:start:](https://url/a.png)\nmiddle\n![:end:](https://url/b.png)"
        expected = ":start:\nmiddle\n:end:"
        self.assertEqual(normalize_markdown_images(input_text), expected)

    def test_no_emoji(self):
        input_text = "Just plain text"
        self.assertEqual(normalize_markdown_images(input_text), input_text)

    def test_empty_string(self):
        self.assertEqual(normalize_markdown_images(""), "")

    def test_custom_emoji_with_numbers_and_underscores(self):
        input_text = "![:ship_it_100:](https://emoji.slack-edge.com/T123/ship_it_100/abc.gif)"
        expected = ":ship_it_100:"
        self.assertEqual(normalize_markdown_images(input_text), expected)


class TestProcessFileBlankLines(unittest.TestCase):
    """Test process_file function for blank lines"""

    def test_process_file_makes_changes(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write("```\nline1\n\nline2\n```\n")
            f.flush()
            filepath = Path(f.name)

        try:
            changed, message = process_blank_lines_file(filepath, dry_run=False)
            self.assertTrue(changed)
            self.assertIn("Updated", message)

            content = filepath.read_text()
            self.assertIn("```\nline1\nline2\n```", content)
        finally:
            filepath.unlink()

    def test_process_file_no_changes_needed(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write("just text\nno blank lines\n")
            f.flush()
            filepath = Path(f.name)

        try:
            changed, message = process_blank_lines_file(filepath, dry_run=False)
            self.assertFalse(changed)
            self.assertIn("No changes", message)
        finally:
            filepath.unlink()

    def test_process_file_dry_run(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write("```\nline1\n\nline2\n```\n")
            f.flush()
            filepath = Path(f.name)

        try:
            original_content = filepath.read_text()
            changed, message = process_blank_lines_file(filepath, dry_run=True)
            self.assertTrue(changed)
            self.assertIn("DRY RUN", message)

            # File should not be modified in dry run
            self.assertEqual(filepath.read_text(), original_content)
        finally:
            filepath.unlink()

    def test_process_file_not_found(self):
        filepath = Path("/nonexistent/file.md")
        changed, message = process_blank_lines_file(filepath, dry_run=False)
        self.assertFalse(changed)
        self.assertIn("Error", message)


class TestProcessFileSlackEmoji(unittest.TestCase):
    """Test process_file function for Slack emoji"""

    def test_process_file_with_emoji(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write("Done ![:done:](https://emoji.slack-edge.com/T123/done/abc.png)\n")
            f.flush()
            filepath = Path(f.name)

        try:
            changed, num_replacements = process_slack_emoji_file(filepath, dry_run=False)
            self.assertTrue(changed)
            self.assertGreater(num_replacements, 0)

            content = filepath.read_text()
            self.assertIn("Done :done:", content)
        finally:
            filepath.unlink()

    def test_process_file_multiple_types(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write("Emoji: ![:tada:](https://url/a.png)\n")
            f.write("Zoom: ![Speaker 1](https://us01cnst1.zoom.com/img.png)\n")
            f.write("Base64: ![alt](data:image/png;base64,abc)\n")
            f.flush()
            filepath = Path(f.name)

        try:
            changed, num_replacements = process_slack_emoji_file(filepath, dry_run=False)
            self.assertTrue(changed)
            self.assertEqual(num_replacements, 3)
        finally:
            filepath.unlink()

    def test_process_file_dry_run(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write("Done ![:done:](https://emoji.slack-edge.com/T123/done/abc.png)\n")
            f.flush()
            filepath = Path(f.name)

        try:
            original_content = filepath.read_text()
            changed, num_replacements = process_slack_emoji_file(filepath, dry_run=True)
            self.assertTrue(changed)

            # File should not be modified in dry run
            self.assertEqual(filepath.read_text(), original_content)
        finally:
            filepath.unlink()

    def test_process_file_no_changes(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write("Just plain text\nNo emoji here\n")
            f.flush()
            filepath = Path(f.name)

        try:
            changed, num_replacements = process_slack_emoji_file(filepath, dry_run=False)
            self.assertFalse(changed)
            self.assertEqual(num_replacements, 0)
        finally:
            filepath.unlink()


class TestIntegration(unittest.TestCase):
    """Integration tests combining multiple functions"""

    def test_normalize_whitespace_then_normalize_whitespaces(self):
        input_text = "```\nline1\n  \nline2  \n\n\nline3\n```\ntext"
        # First normalize whitespace
        after_whitespace = normalize_whitespace(input_text)
        # Then remove blank lines in code blocks
        result = normalize_whitespace_in_code_blocks(after_whitespace)
        # Should have removed blank lines from code block and normalized whitespace
        self.assertIn("```\nline1\nline2", result)

    def test_combined_processing(self):
        # Simulate a file with emoji, blank lines, and whitespace issues
        input_text = (
            "Done: ![:done:](https://url/done.png)  \n"
            "```\ncode\n\nmore code\n```\n"
            "Emoji: ![:tada:](https://url/tada.png)\n"
        )

        # Process emoji
        after_emoji = normalize_markdown_images(input_text)
        self.assertIn("Done: :done:", after_emoji)
        self.assertIn("Emoji: :tada:", after_emoji)

    def test_file_with_all_transformations(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write("Emoji: ![:tada:](https://url/tada.png)  \n")
            f.write("```\ncode\n\n\nmore\n```\n")
            f.write("   \n")
            f.write("text\n")
            f.flush()
            filepath = Path(f.name)

        try:
            # First process slack emoji
            changed1, replacements = process_slack_emoji_file(filepath, dry_run=False)
            # Then process blank lines
            changed2, message = process_blank_lines_file(filepath, dry_run=False)

            content = filepath.read_text()
            # Should have emoji converted
            self.assertIn(":tada:", content)
            # Should have blank lines removed from code block
            self.assertIn("```\ncode\nmore\n```", content)
        finally:
            filepath.unlink()


if __name__ == "__main__":
    unittest.main(verbosity=2)
