#!/usr/bin/env python3
"""Unit tests for pdf_lib.py (run: ./pdf-extract.sh --test)."""

import os
import tempfile
import unittest
from pathlib import Path

import pdf_lib as lib


def make_pdf(path: Path, pages_text: list[str], user_pwd: str | None = None,
             owner_pwd: str | None = None, in_form_xobject: bool = False) -> Path:
    """Write a small PDF with one Helvetica text line per page (optionally encrypted)."""
    from pypdf import PdfWriter
    from pypdf.generic import (ArrayObject, DecodedStreamObject, DictionaryObject,
                               FloatObject, NameObject)

    w = PdfWriter()
    for txt in pages_text:
        page = w.add_blank_page(width=612, height=792)
        font = DictionaryObject({
            NameObject("/Type"): NameObject("/Font"),
            NameObject("/Subtype"): NameObject("/Type1"),
            NameObject("/BaseFont"): NameObject("/Helvetica"),
        })
        fonts = DictionaryObject({NameObject("/F1"): w._add_object(font)})
        ops = "".join(
            f"BT /F1 12 Tf 72 {720 - 16 * i} Td ({ln}) Tj ET\n" for i, ln in enumerate(txt.split("\n"))
        ).encode() if txt else b""
        res = DictionaryObject({NameObject("/Font"): fonts})
        if in_form_xobject:
            form = DecodedStreamObject()
            form.set_data(ops)
            form.update({
                NameObject("/Type"): NameObject("/XObject"),
                NameObject("/Subtype"): NameObject("/Form"),
                NameObject("/BBox"): ArrayObject([FloatObject(0), FloatObject(0),
                                                  FloatObject(612), FloatObject(792)]),
                NameObject("/Resources"): DictionaryObject({NameObject("/Font"): fonts}),
            })
            res = DictionaryObject({NameObject("/XObject"): DictionaryObject(
                {NameObject("/Fm1"): w._add_object(form)})})
            ops = b"q /Fm1 Do Q\n"
        content = DecodedStreamObject()
        content.set_data(ops)
        page[NameObject("/Resources")] = res
        page[NameObject("/Contents")] = w._add_object(content)
    w.add_metadata({"/Title": "Sample Doc", "/CreationDate": "D:20240315120000"})
    if user_pwd is not None or owner_pwd is not None:
        w.encrypt(user_password=user_pwd or "", owner_password=owner_pwd or "owner",
                  algorithm="AES-256")
    with open(path, "wb") as f:
        w.write(f)
    return path


class TmpDirCase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()


class TestPaths(TmpDirCase):
    def test_target_md_path_same_stem(self):
        self.assertEqual(lib.target_md_path(Path("/a/b/Annual Report 01.pdf")), Path("/a/b/Annual Report 01.md"))

    def test_target_md_path_suffix(self):
        self.assertEqual(lib.target_md_path(Path("x.PDF"), ".pdf.md"), Path("x.pdf.md"))

    def test_write_atomic_and_sha(self):
        p = self.dir / "f.txt"
        lib.write_text_atomic(p, "héllo")
        self.assertEqual(p.read_text(encoding="utf-8"), "héllo")
        self.assertEqual(len(lib.file_sha256(p)), 64)
        self.assertEqual([f.name for f in self.dir.iterdir()], ["f.txt"])  # no temp left

    def test_frontmatter_and_ownership(self):
        md = self.dir / "a.md"
        md.write_text('---\ngenerator: "pdf-extract"\nsource_sha256: "abc"\n---\n# x\n')
        self.assertEqual(lib.read_frontmatter(md)["source_sha256"], "abc")
        self.assertTrue(lib.is_generated_by_us(md))
        self.assertTrue(lib.is_up_to_date(Path("unused"), md, pdf_sha="abc"))
        self.assertFalse(lib.is_up_to_date(Path("unused"), md, pdf_sha="def"))

    def test_foreign_md_not_ours(self):
        md = self.dir / "b.md"
        md.write_text("# my own notes\n")
        self.assertFalse(lib.is_generated_by_us(md))
        self.assertEqual(lib.read_frontmatter(self.dir / "missing.md"), {})


class TestOpenAndMeta(TmpDirCase):
    def test_open_plain_and_metadata(self):
        pdf = make_pdf(self.dir / "a.pdf", ["Hello World", "Second page"])
        meta = lib.pdf_metadata(lib.open_pdf(pdf))
        self.assertEqual(meta["pages"], 2)
        self.assertEqual(meta["title"], "Sample Doc")
        self.assertEqual(meta["created"], "2024-03-15")
        self.assertFalse(meta["encrypted"])

    def test_owner_only_encryption_opens_with_empty_password(self):
        pdf = make_pdf(self.dir / "o.pdf", ["Secret text here"], owner_pwd="own")
        reader = lib.open_pdf(pdf)
        self.assertIn("Secret", lib.extract_page_text(reader.pages[0], "plain"))

    def test_user_password_locked_then_opened(self):
        pdf = make_pdf(self.dir / "u.pdf", ["Locked text"], user_pwd="s3cret")
        with self.assertRaises(lib.PdfLockedError):
            lib.open_pdf(pdf, ["wrong"])
        reader = lib.open_pdf(pdf, ["wrong", "s3cret"])
        self.assertIn("Locked", lib.extract_page_text(reader.pages[0], "plain"))


class TestExtraction(TmpDirCase):
    def test_best_prefers_layout_when_equal(self):
        pdf = make_pdf(self.dir / "a.pdf", ["Gross pay 1,000.00"])
        text, method = lib.extract_page_best(lib.open_pdf(pdf).pages[0])
        self.assertIn("1,000.00", text)
        self.assertEqual(method, "layout")

    def test_best_handles_form_xobject(self):
        pdf = make_pdf(self.dir / "x.pdf", ["Nested form text"], in_form_xobject=True)
        text, method = lib.extract_page_best(lib.open_pdf(pdf).pages[0])
        self.assertIn("Nested form text", text)
        self.assertIn(method, ("layout", "plain"))

    def test_blank_page_has_no_text(self):
        pdf = make_pdf(self.dir / "b.pdf", [""])
        text, method = lib.extract_page_best(lib.open_pdf(pdf).pages[0])
        self.assertFalse(lib.has_enough_text(text))
        self.assertEqual(method, "none")

    def test_count_and_threshold(self):
        self.assertEqual(lib.count_chars(" a b\n c "), 3)
        self.assertTrue(lib.has_enough_text("x" * 20))
        self.assertFalse(lib.has_enough_text("x" * 19))

    def test_clean_text(self):
        raw = "\n\nA   \r\nB\n\n\n\n\nC\x0cD   E"
        self.assertEqual(lib.clean_text(raw), "A\nB\n\nC\nD   E")
        self.assertEqual(lib.clean_text("D     E", squeeze_spaces=True), "D  E")


class TestRender(unittest.TestCase):
    def setUp(self):
        self.meta = {"title": None, "pages": 2, "encrypted": False}
        self.pages = [lib.PageResult(1, "Line  1\nLine 2", "layout"),
                      lib.PageResult(2, "", "none", ["OCR needed but no backend available"])]

    def test_frontmatter_and_sections(self):
        md = lib.render_markdown("Pay 01.pdf", self.meta, self.pages, "f" * 64,
                                 extracted_at="2026-01-01T00:00:00")
        self.assertTrue(md.startswith("---\nsource: \"Pay 01.pdf\"\n"))
        self.assertIn('generator: "pdf-extract"', md)
        self.assertIn('methods: "layout,none"', md)
        self.assertIn("# Pay 01\n", md)
        self.assertIn("## Page 1\n\n<!-- method: layout -->\n\n```text\nLine  1\nLine 2\n```", md)
        self.assertIn("_(no text found on this page)_", md)
        self.assertIn("OCR needed", md)

    def test_raw_body_and_fence_escape(self):
        md = lib.render_markdown("a.pdf", self.meta, [lib.PageResult(1, "x", "plain")], "0", body="raw")
        self.assertNotIn("```text", md)
        md = lib.render_markdown("a.pdf", self.meta, [lib.PageResult(1, "a ``` b", "plain")], "0")
        self.assertIn("````text\na ``` b\n````", md)

    def test_roundtrip_frontmatter(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "a.md"
            p.write_text(lib.render_markdown("a.pdf", self.meta, self.pages, "abc"))
            self.assertEqual(lib.read_frontmatter(p)["source_sha256"], "abc")


@unittest.skipUnless(lib.ocr_backend() and os.environ.get("PDF_EXTRACT_TEST_OCR"),
                     "set PDF_EXTRACT_TEST_OCR=1 to run the (slow) OCR test")
class TestOcr(TmpDirCase):
    def test_ocr_reads_rendered_text(self):
        pdf = make_pdf(self.dir / "o.pdf", ["OCR SAMPLE TEXT 12345"])
        out = lib.ocr_pages(pdf, [1])
        self.assertIn("12345", out[1])


if __name__ == "__main__":
    unittest.main()
