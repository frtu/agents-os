"""Tests for scan_repo. Run: ./architecture-reverse-engineering.sh --test"""

from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

import scan_repo
from _fixture import make_repo


def run(argv):
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        code = scan_repo.main(argv)
    return code, out.getvalue(), err.getvalue()


class ScanRepoTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = make_repo(Path(self.tmp.name))

    def tearDown(self):
        self.tmp.cleanup()

    def scan(self, *extra, local=False):
        code, out, _ = run([str(self.root), "--json", *([] if local else ["--no-local"]), *extra])
        self.assertEqual(code, 0)
        return json.loads(out)

    def test_buckets_found(self):
        report = self.scan()
        cats = {h["category"] for h in report["hits"]}
        for expected in ("endpoint", "http-client", "database", "queue", "cloud-sdk", "peer-url"):
            self.assertIn(expected, cats)

    def test_skips_and_secrets(self):
        report = self.scan()
        paths = {h["path"] for h in report["hits"]}
        self.assertFalse(any(p.startswith(("build/", "node_modules/")) or p == ".env" for p in paths))
        self.assertNotIn("hunter2", json.dumps(report))
        self.assertNotIn("do-not-read", json.dumps(report))
        self.assertEqual(report["summary"]["files_skipped"]["binary"], 0)  # .bin has no kind

    def test_runtime_specs(self):
        specs = {(s["spec"], s["value"]) for s in self.scan()["runtime_specs"]}
        self.assertIn(("base-image", "zulu-openjdk:21-jre"), specs)
        self.assertIn(("jvm-toolchain", "21"), specs)
        self.assertIn(("spring-boot", "3.3.1"), specs)
        self.assertIn(("kotlin", "1.9.24"), specs)

    def test_inventory(self):
        inv = {i["path"] for i in self.scan()["inventory"]}
        self.assertTrue({"README.md", "build.gradle.kts", "Dockerfile"} <= inv)

    def test_filters_and_cap(self):
        report = self.scan("--bucket", "middleware", "--tier", "confident", "--max-hits", "1")
        self.assertTrue(all(h["bucket"] == "middleware" for h in report["hits"]))
        self.assertTrue(all(h["tier"] == "confident" for h in report["hits"]))
        per_cat = {}
        for h in report["hits"]:
            per_cat[h["category"]] = per_cat.get(h["category"], 0) + 1
        self.assertTrue(all(n == 1 for n in per_cat.values()))

    def test_local_overlay(self):
        overlay = self.root / "local.json"
        overlay.write_text(json.dumps({"categories": {"acme": {
            "bucket": "downstream-peer", "patterns": ["payments\\.internal"]}}}), encoding="utf-8")
        report = self.scan("--signals-local", str(overlay), local=True)
        self.assertIn("acme", {h["category"] for h in report["hits"]})
        self.assertEqual(len(report["signals"]), 2)

    def test_text_mode(self):
        code, out, _ = run([str(self.root), "--no-local"])
        self.assertEqual(code, 0)
        self.assertIn("[runtime-specs]", out)
        self.assertIn("[upstream]", out)

    def test_invalid_repo(self):
        code, _, err = run([str(self.root / "missing"), "--no-local"])
        self.assertEqual(code, 1)
        self.assertIn("not a directory", err)

    def test_missing_overlay_is_error(self):
        code, _, err = run([str(self.root), "--signals-local", str(self.root / "nope.json")])
        self.assertEqual(code, 1)
        self.assertIn("overlay not found", err)


if __name__ == "__main__":
    unittest.main()
