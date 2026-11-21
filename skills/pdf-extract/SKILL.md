---
name: pdf-extract
description: >
  Extract the full text of PDFs into a Markdown file written next to each PDF,
  with the same file name (`Report.pdf` -> `Report.md`). Handles text PDFs,
  text nested in form objects, owner-locked/encrypted PDFs, and scanned pages
  (OCR fallback). Use when the user says "extract this PDF", "convert PDFs to
  markdown", "make an md next to each pdf", "PDF to text", or points at a folder
  of PDFs (invoices, statements, reports) to read or ingest. Produces a faithful
  raw transcript; for summarising or filing the content into a wiki, run
  /second-brain-ingest on the .md afterwards.
allowed-tools: Bash(*pdf-extract/scripts/pdf-extract.sh*) Read
version: 1.0.0
---

# PDF Extract

Turn each PDF into a full-text `.md` with the same name in the same folder. This file
only **calls** the scripts. All the extraction logic and decisions live in `scripts/`.

## Files

| File | Load when |
| --- | --- |
| `scripts/pdf-extract.sh` | Always: the single entry point (creates its own venv on first run) |
| `references/usage.md` | When you need an option not listed below, the output format, the status meanings, or reuse of the library from another skill |

Never read the Python sources to run the skill. The `--help` output and `references/usage.md` are enough.

## Process

1. **Resolve inputs.** Collect the PDF files and/or folders the user named. Ask once only if none was given. Add `-r` if the user says "and sub-folders" / "recursively".
2. **Preview (optional).** For a large folder, or when `.md` files already exist there, run a dry run first and show the user the summary:
   ```bash
   <skills-dir>/pdf-extract/scripts/pdf-extract.sh "<path>" [-r] --dry-run --json
   ```
3. **Run.**
   ```bash
   <skills-dir>/pdf-extract/scripts/pdf-extract.sh "<path>" [...] [-r] --json
   ```
   Pass through only what the user asked for:
   - `--force`: regenerate even when up to date, or overwrite a hand-written `.md`
   - `--ocr always|never`: force or forbid OCR (default `auto` = only pages with no text)
   - `--languages "en-US,fr-FR,zh-Hans"`: OCR languages when known
   - `--body raw`: prose output instead of fenced blocks (for prose-only documents)
   - Passwords: ask the user to export `PDF_EXTRACT_PASSWORD` in their shell. Don't put a password in a command line you show or log.
4. **Report.** Read the JSON `summary` and turn it into a short report: counts by status, then one line for each PDF that is `locked`, `error`, `written-empty`, or has `notes`. Do not print the extracted text unless the user asks.
5. **Follow up on failures:**
   - `locked` → ask for the password, then re-run that file with `PDF_EXTRACT_PASSWORD` set.
   - `written-empty` / "OCR needed but no backend" → tell the user OCR is unavailable (macOS Vision, or `tesseract` + `pdftoppm`).
   - `skipped-foreign` → a `.md` the tool didn't write already exists. Re-run with `--force` only after the user confirms it can be overwritten.

## Rules

- The script never overwrites a `.md` it didn't generate unless `--force` is passed, and it skips PDFs whose `.md` is already up to date (checked by SHA-256). Re-running is safe and cheap.
- Output is a faithful transcript: no summarising, reformatting or "fixing" of numbers. Interpretation belongs to the next step.
- PDFs often hold personal data (payslips, IDs). Keep the extracted text local: don't paste it into external services.

## Chaining

- `/lint-unformat`: clean up the Markdown if it will be kept as a document.
