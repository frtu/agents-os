#!/usr/bin/env python3
"""Unit tests for pdf_to_md.py — the orchestrator's decisions (run: ./pdf-extract.sh --test)."""

import io
import json
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock

import pdf_lib as lib
import pdf_to_md as orch
from test_pdf_lib import make_pdf


def run(argv):
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        code = orch.main(argv)
    return code, out.getvalue()


class OrchestratorCase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def report(self, argv):
        code, out = run([*argv, "--json"])
        return code, json.loads(out)


class TestDiscovery(OrchestratorCase):
    def test_flat_vs_recursive_and_hidden(self):
        make_pdf(self.dir / "a.pdf", ["A text content here"])
        (self.dir / "sub").mkdir()
        make_pdf(self.dir / "sub" / "b.PDF", ["B text content here"])
        (self.dir / ".hidden").mkdir()
        make_pdf(self.dir / ".hidden" / "c.pdf", ["C"])
        (self.dir / "notes.txt").write_text("x")
        self.assertEqual([p.name for p in orch.discover_pdfs([str(self.dir)], False)], ["a.pdf"])
        self.assertEqual(sorted(p.name for p in orch.discover_pdfs([str(self.dir)], True)),
                         ["a.pdf", "b.PDF"])


class TestDecisions(OrchestratorCase):
    def test_writes_md_next_to_pdf(self):
        pdf = make_pdf(self.dir / "Pay Jan.pdf", ["Basic pay 18,000.00"])
        code, rep = self.report([str(pdf), "--ocr", "never"])
        self.assertEqual(code, 0)
        self.assertEqual(rep["results"][0]["status"], "written")
        md = (self.dir / "Pay Jan.md").read_text()
        self.assertIn("18,000.00", md)
        self.assertTrue(lib.is_up_to_date(pdf, self.dir / "Pay Jan.md"))

    def test_second_run_skips_then_force_rewrites(self):
        pdf = make_pdf(self.dir / "a.pdf", ["Some text content"])
        self.report([str(pdf), "--ocr", "never"])
        _, rep = self.report([str(pdf), "--ocr", "never"])
        self.assertEqual(rep["results"][0]["status"], "skipped-up-to-date")
        _, rep = self.report([str(pdf), "--ocr", "never", "--force"])
        self.assertEqual(rep["results"][0]["status"], "written")

    def test_changed_pdf_is_regenerated(self):
        pdf = make_pdf(self.dir / "a.pdf", ["Version one text"])
        self.report([str(pdf), "--ocr", "never"])
        make_pdf(pdf, ["Version two text"])
        _, rep = self.report([str(pdf), "--ocr", "never"])
        self.assertEqual(rep["results"][0]["status"], "written")
        self.assertIn("Version two", (self.dir / "a.md").read_text())

    def test_foreign_md_is_protected(self):
        pdf = make_pdf(self.dir / "a.pdf", ["Text content here"])
        (self.dir / "a.md").write_text("# hand-written notes\n")
        _, rep = self.report([str(pdf), "--ocr", "never"])
        self.assertEqual(rep["results"][0]["status"], "skipped-foreign")
        self.assertEqual((self.dir / "a.md").read_text(), "# hand-written notes\n")

    def test_dry_run_writes_nothing(self):
        pdf = make_pdf(self.dir / "a.pdf", ["Text content here"])
        _, rep = self.report([str(pdf), "--dry-run", "--ocr", "never"])
        self.assertEqual(rep["results"][0]["status"], "dry-run")
        self.assertFalse((self.dir / "a.md").exists())

    def test_locked_pdf_reports_and_exit_2(self):
        pdf = make_pdf(self.dir / "l.pdf", ["Locked text"], user_pwd="pw")
        code, rep = self.report([str(pdf), "--ocr", "never"])
        self.assertEqual((code, rep["results"][0]["status"]), (2, "locked"))
        code, rep = self.report([str(pdf), "--ocr", "never", "--password", "pw"])
        self.assertEqual((code, rep["results"][0]["status"]), (0, "written"))

    def test_password_from_env(self):
        pdf = make_pdf(self.dir / "l.pdf", ["Locked text"], user_pwd="pw")
        with mock.patch.dict("os.environ", {"PDF_EXTRACT_PASSWORD": "pw"}):
            code, rep = self.report([str(pdf), "--ocr", "never"])
        self.assertEqual(rep["results"][0]["status"], "written")

    def test_corrupt_pdf_is_error_not_crash(self):
        bad = self.dir / "bad.pdf"
        bad.write_bytes(b"not a pdf")
        make_pdf(self.dir / "good.pdf", ["Good text content"])
        code, rep = self.report([str(self.dir), "--ocr", "never"])
        st = {Path(r["pdf"]).name: r["status"] for r in rep["results"]}
        self.assertEqual(st, {"bad.pdf": "error", "good.pdf": "written"})
        self.assertEqual(code, 2)


class TestOcrPolicy(OrchestratorCase):
    def test_auto_ocr_only_pages_without_text(self):
        pdf = make_pdf(self.dir / "m.pdf", ["Page one has plenty of text", ""])
        with mock.patch.object(lib, "ocr_backend", return_value="vision"), \
             mock.patch.object(lib, "ocr_pages", return_value={2: "scanned words here"}) as ocr:
            _, rep = self.report([str(pdf)])
        ocr.assert_called_once()
        self.assertEqual(ocr.call_args.args[1], [2])
        self.assertEqual(rep["results"][0]["methods"], "layout,ocr-vision")

    def test_always_ocr_all_pages_but_keeps_richer_text(self):
        pdf = make_pdf(self.dir / "m.pdf", ["Page one has a long text layer", ""])
        with mock.patch.object(lib, "ocr_backend", return_value="vision"), \
             mock.patch.object(lib, "ocr_pages", return_value={1: "short", 2: "ocr text"}) as ocr:
            _, rep = self.report([str(pdf), "--ocr", "always"])
        self.assertEqual(ocr.call_args.args[1], [1, 2])
        self.assertEqual(rep["results"][0]["methods"], "layout,ocr-vision")

    def test_never_and_no_backend(self):
        pdf = make_pdf(self.dir / "s.pdf", [""])
        with mock.patch.object(lib, "ocr_pages") as ocr:
            _, rep = self.report([str(pdf), "--ocr", "never"])
        ocr.assert_not_called()
        self.assertEqual(rep["results"][0]["status"], "written-empty")
        with mock.patch.object(lib, "ocr_backend", return_value=None):
            _, rep = self.report([str(pdf), "--force"])
        self.assertIn("OCR needed but no backend available", rep["results"][0]["notes"])

    def test_ocr_failure_is_noted_not_fatal(self):
        pdf = make_pdf(self.dir / "s.pdf", [""])
        with mock.patch.object(lib, "ocr_backend", return_value="vision"), \
             mock.patch.object(lib, "ocr_pages", side_effect=RuntimeError("boom")):
            code, rep = self.report([str(pdf)])
        self.assertEqual(code, 0)
        self.assertTrue(any("OCR failed" in n for n in rep["results"][0]["notes"]))


if __name__ == "__main__":
    unittest.main()
