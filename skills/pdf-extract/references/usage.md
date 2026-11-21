# pdf-extract — usage reference (humans & AI agents)

Writes `<name>.md` next to every `<name>.pdf`, holding the full text of every page.

- **Humans** read [Quick start](#quick-start) and [Options](#options).
- **Agents** read [Agent contract](#agent-contract): run with `--json`, then act on `status`.

## Quick start

```bash
S=<skills-dir>/pdf-extract/scripts

$S/pdf-extract.sh ~/Documents/reports             # every PDF in the folder
$S/pdf-extract.sh ~/Documents -r                  # … and in sub-folders
$S/pdf-extract.sh a.pdf b.pdf                     # specific files
$S/pdf-extract.sh ~/Documents/reports --dry-run   # what would happen, writes nothing
$S/pdf-extract.sh --test                          # unit tests
```

On the first run, `pdf-extract.sh` creates a private venv (`~/.cache/pdf-extract/venv`) and installs
`scripts/requirements.txt` from binary wheels only, so no compiler is needed. When
`requirements.txt` changes, the next run reinstalls automatically.

Run it again at any time: unchanged PDFs are skipped (`skipped-up-to-date`).

## Options

| Option | Default | Effect |
| --- | --- | --- |
| `-r`, `--recursive` | off | Also process sub-folders (hidden folders are always skipped) |
| `-f`, `--force` | off | Rewrite even if up to date, **and** overwrite `.md` files the tool did not create |
| `-n`, `--dry-run` | off | Extract and report, write nothing |
| `--ocr auto\|always\|never` | `auto` | `auto`: OCR only pages whose text layer has fewer than `--min-chars` characters. `always`: OCR every page and keep the richer result |
| `--min-chars N` | `20` | Below this many non-space characters, a page counts as "no text" |
| `--languages L` | auto-detect | OCR languages: Vision `en-US,fr-FR,zh-Hans`; tesseract `eng,fra,chi_sim` |
| `--prefer layout\|plain` | `layout` | Preferred text mode when both modes find text |
| `--body fenced\|raw` | `fenced` | `fenced` keeps column alignment inside a ```` ```text ```` block. `raw` writes the text as Markdown prose |
| `--squeeze` | off | Collapse runs of 3 or more spaces (smaller file, loses alignment) |
| `--suffix S` | `.md` | Output suffix, e.g. `.pdf.md` to avoid clashing with existing notes |
| `--template PATH` | `references/templates/markdown-output.md` | Output template for the Markdown body (see [Output format](#output-format)) |
| `--password P` | none | **Explicit override** for one run: password to try on encrypted PDFs (repeatable). The normal source is `$PDF_EXTRACT_PASSWORD` |
| `--json` | off | Machine-readable report on stdout. Progress goes to stderr |
| `-q`, `--quiet` | off | Print the summary line only |

### Environment variables

| Variable | Default | Purpose |
| --- | --- | --- |
| `PDF_EXTRACT_VENV` | `~/.cache/pdf-extract/venv` | Where the venv lives |
| `PDF_EXTRACT_CACHE` | `~/.cache/pdf-extract` | Holds the compiled macOS OCR helper |
| `PDF_EXTRACT_PASSWORD` | none | Password tried on encrypted PDFs: the default way to pass it |
| `PDF_EXTRACT_ENV_FILE` | `~/.config/pdf-extract/.env` | Optional `KEY=VALUE` file loaded by `pdf-extract.sh` before anything else (only `PDF_EXTRACT_*` keys; a variable already set in the shell wins). Template: [`.env.example`](./.env.example) |
| `PDF_EXTRACT_PYTHON` | `python3` | Interpreter used to create the venv |
| `PDF_EXTRACT_TEST_OCR` | unset | Set to `1` to include the slow real-OCR test in `--test` |

### Passwords

The script always reads the password from `PDF_EXTRACT_PASSWORD`. Highest precedence first:

1. **Explicit override:** `--password '…'` on the command line, or a password the user explicitly gives the agent (the agent passes it inline as `PDF_EXTRACT_PASSWORD='…'` for that run only)
2. `PDF_EXTRACT_PASSWORD` already set in the shell
3. Optional `~/.config/pdf-extract/.env`, loaded by `pdf-extract.sh`

```bash
# Optional, once: a private .env file (start from the example)
mkdir -p ~/.config/pdf-extract
cp <skills-dir>/pdf-extract/references/.env.example ~/.config/pdf-extract/.env
chmod 600 ~/.config/pdf-extract/.env          # then edit PDF_EXTRACT_PASSWORD in your editor

# One-off override
$S/pdf-extract.sh locked.pdf --password '…'
```

No password works → status `locked`. Nothing ever prompts. Agents never guess a password. Rules: `_references_/secret-configuration.md` in the skills library.

## How each PDF is handled

```text
path missing, or a file that isn't a PDF ..... invalid-input
.md exists, not made by pdf-extract ......... skipped-foreign      (unless --force)
.md made by us from the same PDF (sha256) ... skipped-up-to-date   (unless --force)
encrypted ................................... try "" (owner-only lock), then the passwords → else locked
each page ................................... pypdf "layout" vs "plain": keep the richer one
  page still has < --min-chars characters ... OCR it (macOS Vision, else tesseract+pdftoppm)
write <name>.md atomically .................. written | written-empty (no text anywhere)
```

Why two text modes: `layout` keeps columns aligned (tables, invoices, forms) but misses text
nested inside Form XObjects. `plain` reads those. Picking per page covers both kinds of PDF.

## Output format

The frontmatter is built in code (it's a machine contract: `source_sha256` and `generator` drive the skip/overwrite decisions). The body comes from [`templates/markdown-output.md`](./templates/markdown-output.md): edit it to change headings or the per-page layout, no code change needed. Placeholders: `{{TITLE}}`, `{{PAGES}}`, `{{PAGE_NUMBER}}`, `{{METHOD}}`, `{{TEXT}}`. Already-extracted files keep their old body until the PDF changes, so re-run with `--force` to apply a template edit. With the default template:

```markdown
---
source: "sample-report.pdf"
source_sha256: "…"            # used to detect changes on re-run
generator: "pdf-extract"      # marks the file as safe to regenerate
generator_version: "1.0.0"
extracted_at: "2024-01-01T12:00:00"
pages: 1
methods: "plain"              # per-page methods used: layout, plain, ocr-vision, ocr-tesseract, none
pdf_title: ""
pdf_author: ""
pdf_producer: ""
pdf_created: "2024-01-01"
encrypted: false
---

# <PDF title or file name>

## Page 1

<!-- method: plain -->

```text
…full page text…
```
```

## Agent contract

Run with `--json`. Stdout is a single JSON document:

```json
{
  "summary": {"written": 47, "skipped-up-to-date": 2},
  "results": [
    {"pdf": "/abs/a.pdf", "md": "/abs/a.md", "status": "written",
     "pages": 1, "methods": "plain", "chars": 612,
     "notes": ["…optional…"], "error": "…only when status=error…"}
  ]
}
```

| `status` | Meaning | Agent action |
| --- | --- | --- |
| `written` | `.md` created or updated | none |
| `written-empty` | Written, but no text found (no OCR available, or OCR returned nothing) | Report it. Suggest OCR setup |
| `dry-run` | Would be written | none |
| `skipped-up-to-date` | Already extracted from this exact PDF | none |
| `skipped-foreign` | A `.md` the tool didn't write exists | Ask before `--force` |
| `locked` | Encrypted, no working password | Ask the user to set `PDF_EXTRACT_PASSWORD` (shell or `.env`), or to give the password explicitly; then re-run. Never guess |
| `error` | Unreadable or corrupt PDF; see `error` | Report it |
| `invalid-input` | The input path doesn't exist, or is a file that isn't a PDF; see `error` (`not found` / `not a PDF or directory`) | Check the path with the user |

`notes` lists non-fatal issues, such as `OCR needed but no backend available` or `OCR failed: …`.

Exit codes: `0` = everything written or skipped · `1` = bad arguments, unreadable template, or an `invalid-input` · `2` = at least one `locked` or `error` (wins over `1`).

## Reusing the library from another skill

`scripts/pdf_lib.py` holds small single-purpose functions, with no loops over files and no CLI:

| Function | Does |
| --- | --- |
| `target_md_path(pdf, suffix=".md")` | Output path next to the PDF |
| `file_sha256(path)` · `write_text_atomic(path, text)` | Hashing, safe write |
| `read_frontmatter(md)` · `is_generated_by_us(md)` · `is_up_to_date(pdf, md, sha)` | Ownership and staleness checks |
| `open_pdf(pdf, passwords)` → reader (raises `PdfLockedError`) | Open and decrypt |
| `pdf_metadata(reader)` | Title, author, producer, created, pages, encrypted |
| `extract_page_text(page, "layout"\|"plain")` · `extract_page_best(page)` | Text layer |
| `count_chars` · `has_enough_text` · `clean_text` | Text helpers |
| `ocr_backend()` · `ocr_pages(pdf, [1,3], backend, languages)` | OCR |
| `PageResult` · `render_markdown(name, meta, pages, sha, body, template=None)` | Markdown output |
| `load_template(path=None)` · `fill(text, values)` | Read an output template (raises `ValueError` if a section is missing) · fill `{{PLACEHOLDERS}}` in one pass |

```python
import sys; sys.path.insert(0, "<skills-dir>/pdf-extract/scripts")
import pdf_lib as lib
reader = lib.open_pdf("x.pdf")
text, method = lib.extract_page_best(reader.pages[0])
```

Run it with the skill's venv interpreter (`~/.cache/pdf-extract/venv/bin/python`) so `pypdf` is available.

## Files

```text
pdf-extract/
├── SKILL.md                 # caller only: when to run, which flags, how to report
├── references/
│   ├── usage.md             # this file
│   ├── .env.example         # every PDF_EXTRACT_* key, placeholders (copy to ~/.config/pdf-extract/.env)
│   └── templates/markdown-output.md   # body format of the generated .md (edit freely)
└── scripts/
    ├── pdf-extract.sh       # entry point: .env loading + venv bootstrap + run / --test
    ├── pdf_to_md.py         # orchestrator: discovery, loops, skip/OCR decisions, report
    ├── pdf_lib.py           # low-level reusable functions
    ├── ocr_macos.swift      # Vision OCR helper (compiled once into the cache)
    ├── requirements.txt     # pypdf, pycryptodome (binary wheels)
    ├── test_pdf_lib.py
    ├── test_pdf_to_md.py
    └── test_pdf_extract_sh.py   # entry point: --help, .env loading
```
