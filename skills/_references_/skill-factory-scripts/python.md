# Skill factory — Python script conventions

**Load in write mode** when you write or change a `.py` file in a skill's `scripts/`. General `scripts/` rules (what goes there, layers, CLI interface, tests) are in [`rules.md`](./rules.md); how a shell entry point launches Python is in [`bash.md`](./bash.md). Reference implementation: `pdf-extract/scripts/` (`pdf_lib.py`, `pdf_to_md.py`, `test_*.py`, `requirements.txt`).

## 1. Dependencies and the venv

| Situation | Rule |
| --- | --- |
| **Standard library only** (preferred) | No `requirements.txt`, no venv. Run with `python3 {script}.py` directly, or through a thin entry point |
| **Third-party packages** | List them in `scripts/requirements.txt`. Install them **only** into a private venv at `~/.cache/{skill}/venv`, created by the entry point (see [`bash.md`](./bash.md) §3). Never `pip install` into the user's global or system Python, never `--user` |
| **Optional package** (enhances, not required) | Import it inside the function that needs it, inside `try/except ImportError`, and degrade with a clear message (what's missing, what is lost, how to install) |
| **External binary** (`tesseract`, `swiftc`) | Detect with `shutil.which()`; choose a backend or report "not available". Never assume it's installed |
| **Compiled helper** (Swift, C) | Ship the source in `scripts/`, compile once into `~/.cache/{skill}/`, recompile when the source is newer (`pdf_lib._vision_binary`) |

`requirements.txt` rules:

- One package per line with a **lower bound** (`pypdf>=4.0`), plus a comment saying why it's there when it isn't obvious.
- Prefer packages with **binary wheels** for macOS and Linux. The entry point installs with `--only-binary=:all:`, so no compiler or Rust toolchain is needed. If a package would build from source, pick an alternative and say so in a comment (`pycryptodome` over `cryptography`).
- Changing the file is enough to trigger a reinstall: the entry point compares its SHA-256 with a stamp in the venv.

Cache and state paths: anything written at runtime (venv, compiled helpers, logs, calibration data) goes under `~/.cache/{skill}/`, overridable with `{SKILL}_CACHE` / `{SKILL}_VENV`. **Never write into the skill folder**: it's a symlinked, version-controlled install.

## 2. File layout

Every script follows this order:

```python
#!/usr/bin/env python3
"""
{script} — {one-line role: util library | orchestrator | gate}.

{What it does, in 2–5 lines. For a CLI: usage line, decision flow, statuses, exit codes.}

    python3 {script}.py <inputs> [options]

Exit code: 0 = OK, 1 = …, 2 = ….
"""

from __future__ import annotations      # modern type hints on Python 3.9+

import argparse                          # 1. stdlib, alphabetical
import json
import os
import sys
from pathlib import Path

import {domain}_lib as lib               # 2. local modules (same folder); third-party imported where needed

GENERATOR = "{skill}"                     # 3. constants, UPPER_SNAKE
SCRIPTS_DIR = Path(__file__).resolve().parent
CACHE_DIR = Path(os.environ.get("{SKILL}_CACHE", Path.home() / ".cache" / "{skill}"))


# --------------------------------------------------------------------------- #
# {Group name}                             4. functions grouped under banners
# --------------------------------------------------------------------------- #

def parse_args(argv: list[str] | None = None) -> argparse.Namespace: ...

def main(argv: list[str] | None = None) -> int: ...

if __name__ == "__main__":                 # 5. no work at import time
    sys.exit(main())
```

- The **module docstring** is the script's documentation. A library lists its function groups (`pdf_lib.py` header). A CLI states usage, decision flow, statuses and exit codes, and passes it to `argparse` (see §4).
- **Naming:** `snake_case` files and functions, `UPPER_SNAKE` constants, `PascalCase` classes and dataclasses, a leading `_` for private helpers. Library modules end in `_lib.py` and are imported as `import {domain}_lib as lib`.
- **No side effects at import**: no I/O, no argument parsing, no `print`. Tests and other skills must be able to import the module safely.
- **Larger skills** may use packages (`scripts/{pkg}/__init__.py` + `__main__.py`, run with `python -m {pkg}`; tests in `scripts/tests/`). The entry point then sets `PYTHONPATH="$SCRIPT_DIR"` (exemplar: `transcribe-voice-memo`).

## 3. Code style

- **Type hints** on every public function; `X | None` and `list[str]` (thanks to `from __future__ import annotations`). A `@dataclass` for structured results (`PageResult`).
- **One-line docstring** on every public function, saying what it returns, with an example when the transformation isn't obvious (`a/b/Report.pdf -> a/b/Report.md`).
- **`pathlib.Path`** for paths, never string concatenation. Accept `Path | str` at the boundary, convert once.
- **Utils raise, orchestrators decide.** A util raises a specific exception (`PdfLockedError`); the orchestrator catches it per item and turns it into a status. Utils never call `sys.exit` or `print`.
- **Subprocess:** argument lists (never `shell=True`), `capture_output=True, text=True`, a `timeout`, and an error message that includes the start of `stderr`.
- **Files:** read and write with `encoding="utf-8"`. Write atomically (temp file in the same folder + `os.replace`). Stream large files (hashing in chunks).
- **JSON:** `json.dumps(..., ensure_ascii=False, indent=2)` for human-readable output; stable key names (they're a machine contract).
- **Environment variables** are read in one place (constants at the top, or `main`), never deep inside utils.
- **Secrets** ([`../secret-configuration.md`](../secret-configuration.md)): read the env var `{SKILL}_{THING}`. An explicit override flag (e.g. `--password`, help text *"explicit override"*) wins when given. Python never parses `.env` itself (the entry point loads it), never prompts (`getpass`), and never prints or logs a secret, including in error messages and JSON reports.
- No global mutable state; pass configuration as arguments.
- Keep formatting consistent with the file you're editing (4-space indentation for new files). Lines up to ~100 characters.

## 4. CLI (`parse_args` + `main`)

```python
def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("inputs", nargs="+", help="files and/or directories")
    ap.add_argument("-n", "--dry-run", action="store_true", help="report, write nothing")
    ap.add_argument("-f", "--force", action="store_true", help="overwrite files we didn't create")
    ap.add_argument("--json", action="store_true", help="print the report as JSON (for agents)")
    ap.add_argument("-q", "--quiet", action="store_true", help="print only the summary")
    return ap.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    results = [process(item, args) for item in discover(args.inputs)]
    print_report(results, args.json, args.quiet)          # results → stdout
    return 2 if any(r["status"] == "error" for r in results) else 0
```

- `parse_args(argv)` and `main(argv) -> int` take an optional `argv`, so tests call `main([...])` directly without a subprocess.
- `description=__doc__` with `RawDescriptionHelpFormatter`: `--help` shows the full docstring (usage, statuses, exit codes). Every option has a `help=` string that names its default.
- Common flag names across skills: `-n/--dry-run`, `-f/--force`, `-r/--recursive`, `-q/--quiet`, `--json`. Repeatable values use `action="append"`.
- Progress goes to `stderr` (`print(..., file=sys.stderr)`); the report goes to `stdout`. With `--json`, `stdout` holds **only** the JSON: `{"summary": {status: count}, "results": [...]}`.
- Return the exit code from `main`; `sys.exit(main())` is the only exit.

## 5. Tests

- One `test_{module}.py` per module, stdlib `unittest`, next to the module (or in `scripts/tests/` for packages). The header says how to run it (`run: ./{skill}.sh --test`).
- **Build fixtures in code**, in a `tempfile.TemporaryDirectory()` created in `setUp` and cleaned in `tearDown`: generate the small PDF, vault or audio stub the test needs (`make_pdf` in `test_pdf_lib.py`). No binary fixtures committed, no real user data, no network.
- Share fixture builders by importing them (`from test_pdf_lib import make_pdf`) or from a `_fixture.py`.
- **Test the orchestrator through `main(argv)`** with `redirect_stdout` / `redirect_stderr`, and assert on exit code, JSON statuses and files on disk.
- Use `unittest.mock` for external binaries and slow backends. Real slow or platform-specific runs are opt-in with an env var (`PDF_EXTRACT_TEST_OCR=1`) and skipped otherwise with `skipUnless`.
- Run everything with `python3 -m unittest discover -s scripts -p 'test_*.py'`, or `{skill}.sh --test` when there's a venv (tests need the same packages).

## 6. Checklist

- [ ] Docstring header with role, usage, statuses, exit codes; `--help` prints it.
- [ ] Stdlib only, or `requirements.txt` with lower bounds + binary wheels, installed only into `~/.cache/{skill}/venv`.
- [ ] No import-time side effects; `main(argv) -> int`; `sys.exit(main())`.
- [ ] Utils raise, orchestrator maps errors to statuses; no `print`/`exit` in utils.
- [ ] Paths via `Path(__file__).resolve().parent` and `~/.cache/{skill}`; nothing written into the skill folder.
- [ ] Tests build their fixtures in temp dirs and pass via the entry point's `--test`.

## Known gaps in existing skills

- `transcribe-voice-memo/scripts/transcribe.sh` writes runtime state into the skill folder (`.mps_failures`); it belongs in `~/.cache/transcribe-voice-memo/`.
