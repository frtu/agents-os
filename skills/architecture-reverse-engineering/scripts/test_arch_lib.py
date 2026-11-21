"""Tests for arch_lib. Run: ./architecture-reverse-engineering.sh --test"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import arch_lib as lib

SKILL_DIR = Path(__file__).resolve().parent.parent
SIGNALS = SKILL_DIR / "config" / "signals.json"
TEMPLATE = SKILL_DIR / "references" / "templates" / "component-diagram.md"


def compiled() -> lib.Compiled:
    return lib.compile_signals(lib.load_signals(SIGNALS))


class ShippedConfigTest(unittest.TestCase):
    def test_signals_parse_and_compile(self):
        data = lib.load_signals(SIGNALS)
        c = lib.compile_signals(data)
        self.assertTrue(c.categories)
        self.assertIn(".env", c.skip_files)

    def test_every_rule_documents_a_field(self):
        data = json.loads(SIGNALS.read_text(encoding="utf-8"))
        for key in data["rules"]:
            self.assertIn(key, data, f"rules documents unknown field {key}")

    def test_template_has_required_headings(self):
        heads = lib.template_headings(TEMPLATE.read_text(encoding="utf-8"))
        self.assertIn("component diagram", heads)
        self.assertIn("runtime specs", heads)


class SignalsTest(unittest.TestCase):
    def test_missing_keys(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "s.json"
            p.write_text('{"version": 1}', encoding="utf-8")
            with self.assertRaises(lib.SignalsError):
                lib.load_signals(p)

    def test_bad_regex_named(self):
        data = lib.load_signals(SIGNALS)
        data["categories"]["cache"]["patterns"].append("(")
        with self.assertRaisesRegex(lib.SignalsError, "categories.cache.patterns"):
            lib.compile_signals(data)

    def test_merge_appends(self):
        base = lib.load_signals(SIGNALS)
        merged = lib.merge_signals(base, {
            "categories": {"cache": {"patterns": ["acme-cache"]},
                           "acme-peer": {"bucket": "downstream-peer", "patterns": ["acme-client"]}},
            "skip_dirs": ["generated"]})
        self.assertIn("acme-cache", merged["categories"]["cache"]["patterns"])
        self.assertIn("\\bredis\\b", merged["categories"]["cache"]["patterns"])
        self.assertIn("acme-peer", merged["categories"])
        self.assertIn("generated", merged["skip_dirs"])
        self.assertNotIn("acme-cache", base["categories"]["cache"]["patterns"])


class FilesTest(unittest.TestCase):
    def test_glob_matches(self):
        self.assertTrue(lib.glob_matches("a/b/Dockerfile", "Dockerfile"))
        self.assertTrue(lib.glob_matches("helm/values.yaml", "helm/*"))
        self.assertTrue(lib.glob_matches("deploy/helm/values.yaml", "helm/*"))
        self.assertFalse(lib.glob_matches("src/helmet.kt", "helm/*"))

    def test_file_kind_order(self):
        c = compiled()
        self.assertEqual(lib.file_kind("package.json", c), "manifest")
        self.assertEqual(lib.file_kind("openapi.yaml", c), "contract")
        self.assertEqual(lib.file_kind("src/application.yml", c), "config")
        self.assertEqual(lib.file_kind("src/A.kt", c), "source")
        self.assertIsNone(lib.file_kind("LICENSE", c))


class ScanTest(unittest.TestCase):
    def setUp(self):
        self.c = compiled()

    def test_redact(self):
        key = self.c.secret_key
        self.assertEqual(lib.redact("  password: hunter2", key), "password: <redacted>")
        self.assertEqual(lib.redact("api_key=abc", key), "api_key=<redacted>")
        self.assertEqual(lib.redact("password: ${DB_PASS}", key), "password: ${DB_PASS}")
        self.assertEqual(lib.redact("url: jdbc:postgresql://db", key), "url: jdbc:postgresql://db")

    def test_scan_text_tiers_and_lines(self):
        text = "redis:\n  host: cache\nredis.port: 6379\ntoken: x\n"
        hits = lib.scan_text(text, "application.yml", "config", self.c)
        redis = [h for h in hits if h.category == "cache"]
        self.assertEqual(len(redis), 1)
        self.assertEqual(redis[0].lines, [1, 3])
        self.assertEqual(redis[0].tier, "confident")
        token = [h for h in hits if h.category == "auth" and h.match == "token"]
        self.assertEqual(token[0].tier, "flag")
        self.assertEqual(token[0].snippet, "token: <redacted>")

    def test_scope_respected(self):
        hits = lib.scan_text("@RestController", "README.md", "docs", self.c)
        self.assertFalse([h for h in hits if h.category == "endpoint"])

    def test_known_noise(self):
        hits = lib.scan_text("see https://example.com/x", "a.yml", "config", self.c)
        self.assertFalse([h for h in hits if h.category == "peer-url"])

    def test_extract_specs(self):
        specs = lib.extract_specs("FROM --platform=linux/amd64 node:20-alpine\nCOPY . /app\n",
                                  "Dockerfile", self.c)
        values = {(s.spec, s.value) for s in specs}
        self.assertIn(("base-image", "node:20-alpine"), values)
        self.assertIn(("image-copy", ". /app"), values)


class DocumentsTest(unittest.TestCase):
    MD = "# T\n\n## Summary\n\nSee `src/a.kt:12` and `build.gradle.kts`, not `1.2.3` or `--json`.\n" \
         "```mermaid\nflowchart TB\n  A[x]\n```\n## Runtime specs [table]\n"

    def test_doc_headings(self):
        self.assertEqual(lib.doc_headings(self.MD), ["summary", "runtime specs"])

    def test_mermaid_blocks(self):
        blocks = lib.mermaid_blocks(self.MD)
        self.assertEqual(len(blocks), 1)
        self.assertEqual(blocks[0][0], 7)

    def test_cited_paths(self):
        self.assertEqual([p for _, p in lib.cited_paths(self.MD)], ["src/a.kt", "build.gradle.kts"])


class MermaidTest(unittest.TestCase):
    def codes(self, text):
        return sorted(f.code for f in lib.lint_mermaid(text))

    def test_clean(self):
        text = ('flowchart TB\n subgraph S["Svc"]\n  api(["API (v1)"]) -->|GET /x (json)| db[(Orders)]\n'
                ' end\n classDef store fill:#fff\n class db store\n')
        self.assertEqual(self.codes(text), [])

    def test_findings(self):
        text = "flowchart TB\n subgraph S\n  a[Peer (x)] --> b[B]\n  b[Other]\n  c:::nope\n"
        self.assertEqual(self.codes(text), ["DUP_ID", "UNBALANCED", "UNKNOWN_CLASS", "UNQUOTED_CHARS"])

    def test_label_text_not_parsed_as_node(self):
        self.assertEqual(self.codes('flowchart TB\n a["see b[x]"] --> b[B]\n'), [])


if __name__ == "__main__":
    unittest.main()
