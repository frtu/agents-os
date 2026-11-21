#!/usr/bin/env python3
"""
pdf_to_md — orchestrator: write a full Markdown file next to every PDF.

High-level only: discovery, loops, skip/overwrite decisions, choosing when
to call OCR, reporting. All transformations live in `pdf_lib.py`; the Markdown
body format lives in `references/templates/markdown-output.md`.

    pdf-extract.sh <file-or-dir> [...] [options]

Per input, the decision flow is:

    path missing, or a file that isn't a PDF . "invalid-input"
    target exists & not ours ............ skip "skipped-foreign" (unless --force)
    target ours & same source sha256 .... skip "skipped-up-to-date" (unless --force)
    encrypted ........................... try "" then --password / $PDF_EXTRACT_PASSWORD
                                          -> "locked" if none works
    per page: pypdf layout vs plain ..... keep the richer one
    page text < --min-chars ............. OCR that page (--ocr auto, default)
    --ocr always ........................ OCR every page;  --ocr never: no OCR
    write <same-name>.md atomically ..... "written" | "written-empty" (or "dry-run")
    unreadable / corrupt PDF ............ "error"

Secrets: the password is read from $PDF_EXTRACT_PASSWORD, optionally pre-filled from
~/.config/pdf-extract/.env by pdf-extract.sh (keys: references/.env.example).
--password is an explicit override for one run. Nothing ever prompts.

Exit code: 0 = all written or skipped
           1 = bad arguments, unreadable template, or an input path is invalid
           2 = at least one PDF is locked or failed (takes precedence over 1)
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import pdf_lib as lib


# --------------------------------------------------------------------------- #
# Discovery
# --------------------------------------------------------------------------- #

def invalid_inputs(inputs: list[str]) -> list[tuple[str, str]]:
    """Return (input, reason) for each input that is neither a PDF file nor a directory."""
    bad = []
    for raw in inputs:
        p = Path(raw).expanduser()
        if not p.exists():
            bad.append((raw, "not found"))
        elif not p.is_dir() and not (p.is_file() and p.suffix.lower() == ".pdf"):
            bad.append((raw, "not a PDF or directory"))
    return bad


def discover_pdfs(inputs: list[str], recursive: bool) -> list[Path]:
    """Expand files/dirs into a sorted, de-duplicated list of PDFs (hidden files skipped).
    Invalid inputs are ignored here; `invalid_inputs` reports them."""
    found: set[Path] = set()
    for raw in inputs:
        p = Path(raw).expanduser()
        if p.is_file() and p.suffix.lower() == ".pdf":
            found.add(p.resolve())
        elif p.is_dir():
            it = p.rglob("*") if recursive else p.iterdir()
            for f in it:
                if f.is_file() and f.suffix.lower() == ".pdf" and not any(
                    part.startswith(".") for part in f.relative_to(p).parts
                ):
                    found.add(f.resolve())
    return sorted(found)


# --------------------------------------------------------------------------- #
# One PDF
# --------------------------------------------------------------------------- #

def decide_skip(pdf: Path, md: Path, sha: str, force: bool) -> str | None:
    """Return a skip status, or None to process."""
    if force or not md.exists():
        return None
    if not lib.is_generated_by_us(md):
        return "skipped-foreign"
    if lib.is_up_to_date(pdf, md, sha):
        return "skipped-up-to-date"
    return None


def extract_pages(pdf: Path, reader, args) -> list[lib.PageResult]:
    """Text layer first, then OCR for pages that need it (per --ocr policy)."""
    pages: list[lib.PageResult] = []
    for i, page in enumerate(reader.pages, start=1):
        text, method = lib.extract_page_best(page, prefer=args.prefer)
        pages.append(lib.PageResult(i, lib.clean_text(text, args.squeeze), method))

    if args.ocr == "never":
        return pages
    need = [p.number for p in pages
            if args.ocr == "always" or not lib.has_enough_text(p.text, args.min_chars)]
    if not need:
        return pages

    backend = lib.ocr_backend()
    if backend is None:
        for p in pages:
            if p.number in need:
                p.notes.append("OCR needed but no backend available")
        return pages
    try:
        ocr = lib.ocr_pages(pdf, need, backend, args.languages)
    except Exception as exc:  # keep the text layer result, report the OCR failure
        for p in pages:
            if p.number in need:
                p.notes.append(f"OCR failed: {exc}")
        return pages
    for p in pages:
        if p.number in ocr and lib.count_chars(ocr[p.number]) > lib.count_chars(p.text):
            p.text, p.method = lib.clean_text(ocr[p.number]), f"ocr-{backend}"
    return pages


def process_pdf(pdf: Path, args, passwords: list[str], template: dict[str, str]) -> dict:
    """Convert one PDF. Returns a result record (never raises)."""
    md = lib.target_md_path(pdf, args.suffix)
    rec = {"pdf": str(pdf), "md": str(md), "status": "", "pages": 0, "methods": "", "chars": 0}
    try:
        sha = lib.file_sha256(pdf)
        skip = decide_skip(pdf, md, sha, args.force)
        if skip:
            rec["status"] = skip
            return rec
        reader = lib.open_pdf(pdf, passwords)
        meta = lib.pdf_metadata(reader)
        pages = extract_pages(pdf, reader, args)
        rec["pages"] = len(pages)
        rec["methods"] = ",".join(sorted({p.method for p in pages}))
        rec["chars"] = sum(lib.count_chars(p.text) for p in pages)
        notes = sorted({n for p in pages for n in p.notes})
        if notes:
            rec["notes"] = notes
        text = lib.render_markdown(pdf.name, meta, pages, sha, body=args.body,
                                  template=template)
        if args.dry_run:
            rec["status"] = "dry-run"
        else:
            lib.write_text_atomic(md, text)
            rec["status"] = "written" if rec["chars"] else "written-empty"
    except lib.PdfLockedError:
        rec["status"] = "locked"
    except Exception as exc:
        rec["status"] = "error"
        rec["error"] = f"{type(exc).__name__}: {exc}"
    return rec


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #

class _Parser(argparse.ArgumentParser):
    """argparse exits 2 on bad arguments; exit 1 instead, so 2 always means a PDF failed."""

    def error(self, message: str) -> None:  # type: ignore[override]
        self.print_usage(sys.stderr)
        self.exit(1, f"{self.prog}: error: {message}\n")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    ap = _Parser(prog="pdf-extract.sh", description=__doc__,
                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("inputs", nargs="+", help="PDF files and/or directories")
    ap.add_argument("-r", "--recursive", action="store_true", help="descend into sub-directories")
    ap.add_argument("-f", "--force", action="store_true",
                    help="overwrite even up-to-date or non-generated .md files")
    ap.add_argument("-n", "--dry-run", action="store_true", help="extract but do not write")
    ap.add_argument("--ocr", choices=["auto", "always", "never"], default="auto",
                    help="auto: OCR pages with too little text (default)")
    ap.add_argument("--min-chars", type=int, default=20,
                    help="a page with fewer non-space chars counts as 'no text' (default 20)")
    ap.add_argument("--languages", default=None,
                    help='OCR languages, e.g. "en-US,fr-FR,zh-Hans" (Vision) or "eng,fra"')
    ap.add_argument("--prefer", choices=["layout", "plain"], default="layout",
                    help="preferred pypdf mode when both yield text (default layout)")
    ap.add_argument("--body", choices=["fenced", "raw"], default="fenced",
                    help="fenced: page text in ```text blocks (keeps alignment, default)")
    ap.add_argument("--squeeze", action="store_true", help="collapse runs of 3+ spaces")
    ap.add_argument("--suffix", default=".md", help='output suffix (default ".md")')
    ap.add_argument("--template", default=None,
                    help="output template (default references/templates/markdown-output.md)")
    ap.add_argument("--password", action="append", default=[],
                    help="explicit override: password to try on encrypted PDFs (repeatable). "
                         "Normal source: $PDF_EXTRACT_PASSWORD")
    ap.add_argument("--json", action="store_true", help="print the report as JSON (for agents)")
    ap.add_argument("-q", "--quiet", action="store_true", help="print only the summary")
    return ap.parse_args(argv)


def print_report(results: list[dict], as_json: bool, quiet: bool) -> None:
    counts: dict[str, int] = {}
    for r in results:
        counts[r["status"]] = counts.get(r["status"], 0) + 1
    if as_json:
        print(json.dumps({"summary": counts, "results": results}, ensure_ascii=False, indent=2))
        return
    if not quiet:
        for r in results:
            extra = r.get("error") or "; ".join(r.get("notes", []))
            line = f"{r['status']:<20} {r['pages']:>3}p  {r['methods'] or '-':<14} {Path(r['pdf']).name}"
            print(line + (f"  ({extra})" if extra else ""))
    print("summary: " + ", ".join(f"{k}={v}" for k, v in sorted(counts.items())) if counts
          else "summary: no PDF found")


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    passwords = list(args.password)
    if os.environ.get("PDF_EXTRACT_PASSWORD"):
        passwords.append(os.environ["PDF_EXTRACT_PASSWORD"])

    try:
        template = lib.load_template(args.template)
    except (OSError, ValueError) as exc:
        print(f"pdf-extract.sh: error: cannot use template: {exc}", file=sys.stderr)
        return 1

    results = [{"pdf": raw, "md": "", "status": "invalid-input", "pages": 0, "methods": "",
                "chars": 0, "error": reason} for raw, reason in invalid_inputs(args.inputs)]
    for pdf in discover_pdfs(args.inputs, args.recursive):
        rec = process_pdf(pdf, args, passwords, template)
        results.append(rec)
        if not args.json and not args.quiet:
            print(f"… {rec['status']}: {pdf.name}", file=sys.stderr)
    print_report(results, args.json, args.quiet)
    if any(r["status"] in ("error", "locked") for r in results):
        return 2
    return 1 if any(r["status"] == "invalid-input" for r in results) else 0


if __name__ == "__main__":
    sys.exit(main())
