#!/usr/bin/env python3
"""
Unit tests for normalize_markdown_images function in normalize_image_links.py
"""

import unittest
from normalize_image_links import normalize_markdown_images


class TestBasicEmoji(unittest.TestCase):
    """Standard emoji patterns"""

    def test_simple_emoji(self):
        input_text = "![:tada:](https://emoji.slack-edge.com/T086B9BTPEJ/tada/abc123.png)"
        self.assertEqual(normalize_markdown_images(input_text), ":tada:")

    def test_emoji_with_surrounding_text(self):
        input_text = "Hello ![:wave:](https://emoji.slack-edge.com/T123/wave/abc.png) world"
        self.assertEqual(normalize_markdown_images(input_text), "Hello :wave: world")

    def test_multiple_emoji_same_line(self):
        input_text = "![:thumbsup:](https://url/a.png) ![:thumbsdown:](https://url/b.png)"
        self.assertEqual(normalize_markdown_images(input_text), ":thumbsup: :thumbsdown:")


class TestAnimatedEmoji(unittest.TestCase):
    """Animated/GIF emoji patterns"""

    def test_animated_emoji_gif(self):
        input_text = "![:tada-animated:](https://emoji.slack-edge.com/T086B9BTPEJ/tada-animated/3743b73b31c22c82.gif)"
        self.assertEqual(normalize_markdown_images(input_text), ":tada-animated:")

    def test_dancing_emoji(self):
        input_text = "![:parrot-dancing:](https://emoji.slack-edge.com/T123/parrot-dancing/abc.gif)"
        self.assertEqual(normalize_markdown_images(input_text), ":parrot-dancing:")


class TestCustomEmoji(unittest.TestCase):
    """Custom workspace emoji"""

    def test_custom_done_emoji(self):
        input_text = "![:done:](https://emoji.slack-edge.com/T086B9BTPEJ/done/c11bf3db1f90897f.jpg)"
        self.assertEqual(normalize_markdown_images(input_text), ":done:")

    def test_custom_emoji_with_underscores(self):
        input_text = "![:ship_it:](https://emoji.slack-edge.com/T123/ship_it/abc.png)"
        self.assertEqual(normalize_markdown_images(input_text), ":ship_it:")

    def test_custom_emoji_with_numbers(self):
        input_text = "![:100:](https://emoji.slack-edge.com/T123/100/abc.png)"
        self.assertEqual(normalize_markdown_images(input_text), ":100:")

    def test_custom_emoji_hyphenated(self):
        input_text = "![:meow-party:](https://emoji.slack-edge.com/T123/meow-party/abc.gif)"
        self.assertEqual(normalize_markdown_images(input_text), ":meow-party:")


class TestBracketedEmoji(unittest.TestCase):
    """Emoji wrapped in square brackets (often used as links)"""

    def test_bracketed_emoji(self):
        input_text = "[![:done:](https://emoji.slack-edge.com/T086B9BTPEJ/done/c11bf3db1f90897f.jpg)]"
        self.assertEqual(normalize_markdown_images(input_text), "[:done:]")

    def test_bracketed_animated_emoji(self):
        input_text = "[![:rocket-launch:](https://emoji.slack-edge.com/T123/rocket-launch/abc.gif)]"
        self.assertEqual(normalize_markdown_images(input_text), "[:rocket-launch:]")

    def test_multiple_bracketed_emoji(self):
        input_text = "[![:check:](https://url/a.png)] [![:x:](https://url/b.png)]"
        self.assertEqual(normalize_markdown_images(input_text), "[:check:] [:x:]")


class TestStatusEmoji(unittest.TestCase):
    """Common status/reaction emoji"""

    def test_white_check_mark(self):
        self.assertEqual(
            normalize_markdown_images("![:white_check_mark:](https://url/a.png)"),
            ":white_check_mark:"
        )

    def test_warning(self):
        self.assertEqual(
            normalize_markdown_images("![:warning:](https://url/b.png)"),
            ":warning:"
        )

    def test_red_circle(self):
        self.assertEqual(
            normalize_markdown_images("![:red_circle:](https://url/c.png)"),
            ":red_circle:"
        )

    def test_large_green_circle(self):
        self.assertEqual(
            normalize_markdown_images("![:large_green_circle:](https://url/d.png)"),
            ":large_green_circle:"
        )

    def test_eyes(self):
        self.assertEqual(
            normalize_markdown_images("![:eyes:](https://url/e.png)"),
            ":eyes:"
        )

    def test_fire(self):
        self.assertEqual(
            normalize_markdown_images("![:fire:](https://url/f.png)"),
            ":fire:"
        )


class TestMixedContent(unittest.TestCase):
    """Mixed patterns in realistic content"""

    def test_markdown_list_with_emoji(self):
        input_text = """- ![:done:](https://url/done.png) Task completed
- ![:wip:](https://url/wip.png) In progress
- ![:blocked:](https://url/blocked.png) Blocked"""
        expected = """- :done: Task completed
- :wip: In progress
- :blocked: Blocked"""
        self.assertEqual(normalize_markdown_images(input_text), expected)

    def test_table_with_emoji(self):
        input_text = "| Status | ![:check:](https://url/a.png) | ![:x:](https://url/b.png) |"
        expected = "| Status | :check: | :x: |"
        self.assertEqual(normalize_markdown_images(input_text), expected)

    def test_mixed_bracketed_and_regular(self):
        input_text = "Regular ![:smile:](https://url/a.png) and bracketed [![:wave:](https://url/b.png)]"
        expected = "Regular :smile: and bracketed [:wave:]"
        self.assertEqual(normalize_markdown_images(input_text), expected)


class TestEdgeCases(unittest.TestCase):
    """Edge cases and boundary conditions"""

    def test_no_emoji(self):
        input_text = "Just plain text without any emoji"
        self.assertEqual(normalize_markdown_images(input_text), input_text)

    def test_standard_markdown_image(self):
        input_text = "![alt text](https://example.com/image.png)"
        self.assertEqual(normalize_markdown_images(input_text), input_text)

    def test_empty_string(self):
        self.assertEqual(normalize_markdown_images(""), "")

    def test_only_colon_not_emoji(self):
        input_text = "Time is 10:30 and ratio is 1:1"
        self.assertEqual(normalize_markdown_images(input_text), input_text)

    def test_preserves_other_markdown(self):
        input_text = "**bold** and _italic_ with ![:emoji:](https://url/a.png)"
        expected = "**bold** and _italic_ with :emoji:"
        self.assertEqual(normalize_markdown_images(input_text), expected)

    def test_emoji_at_line_boundaries(self):
        input_text = """![:start:](https://url/a.png)
middle text
![:end:](https://url/b.png)"""
        expected = """:start:
middle text
:end:"""
        self.assertEqual(normalize_markdown_images(input_text), expected)

    def test_complex_url_with_query_params(self):
        input_text = "![:emoji:](https://emoji.slack-edge.com/T123/emoji/abc.png?v=2&size=64)"
        self.assertEqual(normalize_markdown_images(input_text), ":emoji:")


class TestDifferentURLFormats(unittest.TestCase):
    """Different Slack CDN URL patterns"""

    def test_jpg_extension(self):
        input_text = "![:photo:](https://emoji.slack-edge.com/T123/photo/abc.jpg)"
        self.assertEqual(normalize_markdown_images(input_text), ":photo:")

    def test_jpeg_extension(self):
        input_text = "![:image:](https://emoji.slack-edge.com/T123/image/abc.jpeg)"
        self.assertEqual(normalize_markdown_images(input_text), ":image:")

    def test_gif_extension(self):
        input_text = "![:animated:](https://emoji.slack-edge.com/T123/animated/abc.gif)"
        self.assertEqual(normalize_markdown_images(input_text), ":animated:")

    def test_different_workspace_ids(self):
        cases = [
            "![:test:](https://emoji.slack-edge.com/T086B9BTPEJ/test/abc.png)",
            "![:test:](https://emoji.slack-edge.com/TABCDEFGH/test/abc.png)",
            "![:test:](https://emoji.slack-edge.com/T12345678/test/abc.png)",
        ]
        for input_text in cases:
            self.assertEqual(normalize_markdown_images(input_text), ":test:")


if __name__ == "__main__":
    unittest.main(verbosity=2)
