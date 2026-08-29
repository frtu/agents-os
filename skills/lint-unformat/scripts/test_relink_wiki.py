#!/usr/bin/env python3
"""
Unit tests for relink-wiki.py.
Tests vocabulary building, finding unlinked mentions, and applying links.
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


rw = _load("relink_wiki", "relink-wiki.py")


class TestGenerateVariations(unittest.TestCase):
	def test_slug_with_hyphens(self):
		v = rw.generate_variations("search-service")
		self.assertIn("Search Service", v)
		# SearchService not added if it's same as title_case without spaces

	def test_single_word(self):
		v = rw.generate_variations("ranking")
		self.assertEqual(v, ["Ranking"])

	def test_all_uppercase(self):
		v = rw.generate_variations("cdc")
		self.assertIn("Cdc", v)


class TestFindExistingLinks(unittest.TestCase):
	def test_finds_wikilinks(self):
		content = "[[foo]] and [[bar|Bar]]"
		links = rw.find_existing_links(content)
		self.assertEqual(links, {"foo", "bar"})

	def test_extracts_filename_from_path(self):
		content = "[[dir/file]]"
		links = rw.find_existing_links(content)
		self.assertEqual(links, {"file"})

	def test_empty_content(self):
		self.assertEqual(rw.find_existing_links(""), set())


class TestFindUnlinkedMentions(unittest.TestCase):
	def test_finds_plain_mention(self):
		vocab = {"kafka": ["Kafka"]}
		content = "We use Kafka."
		existing = set()
		unlinked = rw.find_unlinked_mentions(content, vocab, existing)
		self.assertEqual(len(unlinked), 1)
		self.assertEqual(unlinked[0][0], "Kafka")
		self.assertEqual(unlinked[0][1], "kafka")

	def test_skips_already_linked(self):
		vocab = {"kafka": ["Kafka"]}
		content = "[[kafka|Kafka]] is used."
		existing = {"kafka"}
		unlinked = rw.find_unlinked_mentions(content, vocab, existing)
		self.assertEqual(unlinked, [])

	def test_protects_code_block(self):
		vocab = {"kafka": ["Kafka"]}
		content = "```\nKafka is a system\n```"
		existing = set()
		unlinked = rw.find_unlinked_mentions(content, vocab, existing)
		self.assertEqual(unlinked, [])

	def test_protects_inline_code(self):
		vocab = {"kafka": ["Kafka"]}
		content = "Use `Kafka` CLI."
		existing = set()
		unlinked = rw.find_unlinked_mentions(content, vocab, existing)
		self.assertEqual(unlinked, [])

	def test_protects_frontmatter(self):
		vocab = {"kafka": ["Kafka"]}
		content = "---\ntitle: Kafka\n---\nBody."
		existing = set()
		unlinked = rw.find_unlinked_mentions(content, vocab, existing)
		self.assertEqual(unlinked, [])

	def test_deduplicates_by_slug(self):
		vocab = {"kafka": ["Kafka", "kafka"]}
		content = "Kafka and kafka"
		existing = set()
		unlinked = rw.find_unlinked_mentions(content, vocab, existing)
		self.assertEqual(len(unlinked), 1)
		self.assertEqual(unlinked[0][1], "kafka")

	def test_case_insensitive_match(self):
		vocab = {"elasticsearch": ["Elasticsearch"]}
		content = "elasticsearch is a tool"
		existing = set()
		unlinked = rw.find_unlinked_mentions(content, vocab, existing)
		self.assertEqual(len(unlinked), 1)

	def test_acronym_exact_match(self):
		vocab = {"elasticsearch": ["ES"]}
		content = "We use ES."
		existing = set()
		unlinked = rw.find_unlinked_mentions(content, vocab, existing)
		self.assertEqual(len(unlinked), 1)


class TestApplyLinks(unittest.TestCase):
	def test_links_plain_mention(self):
		links = [("Kafka", "kafka", "[[kafka|Kafka]]")]
		result = rw.apply_links("We use Kafka.", links)
		self.assertEqual(result, "We use [[kafka|Kafka]].")

	def test_first_occurrence_only(self):
		links = [("Kafka", "kafka", "[[kafka|Kafka]]")]
		result = rw.apply_links("Kafka and Kafka again.", links)
		self.assertEqual(result.count("[[kafka|Kafka]]"), 1)

	def test_skips_if_first_occurrence_in_code_block(self):
		# If the first match is protected, the link is not applied
		links = [("Kafka", "kafka", "[[kafka|Kafka]]")]
		content = "```\nKafka\n```\nand Kafka."
		result = rw.apply_links(content, links)
		# First occurrence is in code block, so no link applied even for second
		self.assertEqual(result, content)

	def test_skips_if_first_occurrence_in_frontmatter(self):
		links = [("Kafka", "kafka", "[[kafka|Kafka]]")]
		content = "---\ntitle: Kafka\n---\nText Kafka here."
		result = rw.apply_links(content, links)
		# First occurrence is in frontmatter, so no link applied
		self.assertEqual(result, content)

	def test_skips_existing_links(self):
		links = [("Kafka", "kafka", "[[kafka|Kafka]]")]
		content = "[[kafka|Kafka]] is here."
		result = rw.apply_links(content, links)
		self.assertEqual(result, content)


class TestBuildVocabularyAndProcess(unittest.TestCase):
	def _setup_wiki(self):
		tmpdir = tempfile.TemporaryDirectory()
		wiki_root = Path(tmpdir.name)

		for folder in ["concepts", "product"]:
			(wiki_root / folder).mkdir()

		(wiki_root / "concepts" / "kafka.md").write_text("Kafka content")
		(wiki_root / "product" / "search.md").write_text("Search content")

		return tmpdir, wiki_root

	def test_build_vocabulary_finds_pages(self):
		tmpdir, wiki_root = self._setup_wiki()
		try:
			rw.WIKI_ROOT = wiki_root
			vocab = rw.build_vocabulary()
			self.assertIn("kafka", vocab)
			self.assertIn("search", vocab)
			self.assertGreaterEqual(len(vocab["kafka"]), 1)
		finally:
			tmpdir.cleanup()

	def test_process_file_adds_links(self):
		tmpdir, wiki_root = self._setup_wiki()
		try:
			content_path = wiki_root / "concepts" / "note.md"
			content_path.write_text("We use Kafka.")

			rw.WIKI_ROOT = wiki_root
			links = rw.process_file(content_path, vocab=rw.build_vocabulary(), dry_run=False)
			self.assertGreater(links, 0)
			self.assertIn("[[kafka|Kafka]]", content_path.read_text())
		finally:
			tmpdir.cleanup()

	def test_process_file_dry_run(self):
		tmpdir, wiki_root = self._setup_wiki()
		try:
			content_path = wiki_root / "concepts" / "note.md"
			content_path.write_text("We use Kafka.")
			original = content_path.read_text()

			rw.WIKI_ROOT = wiki_root
			links = rw.process_file(content_path, vocab=rw.build_vocabulary(), dry_run=True)
			self.assertGreater(links, 0)
			self.assertEqual(content_path.read_text(), original)
		finally:
			tmpdir.cleanup()

	def test_skips_readme_and_sources(self):
		tmpdir, wiki_root = self._setup_wiki()
		try:
			(wiki_root / "concepts" / "README.md").write_text("Kafka")
			(wiki_root / "sources").mkdir()
			(wiki_root / "sources" / "source.md").write_text("Kafka")

			rw.WIKI_ROOT = wiki_root
			vocab = rw.build_vocabulary()
			self.assertNotIn("readme", vocab)
			self.assertEqual(len(vocab), 2)
		finally:
			tmpdir.cleanup()


if __name__ == "__main__":
	unittest.main(verbosity=2)
