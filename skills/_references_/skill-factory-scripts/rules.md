# Skill factory — `scripts/` folder rules

**Load in write mode** when a skill has, or should have, a `scripts/` folder. These are the **rules** (what every script must do). The **pattern** behind them (why three layers, exemplar walkthrough, adoption checklist) is in [`script-layering.md`](./script-layering.md). Conventions in [`../../README.md`](../../README.md) → *Scripts* stay the source of truth; this file details them.

## 1. What goes in `scripts/`

- **Every deterministic step**: same input → same output (parse, convert, check, move, count, diff, render a template). Not prose in `SKILL.md` for the agent to redo by hand.
- **Not judgement**: reading comprehension, taste, choosing between options, asking the user. That stays in `SKILL.md`.
- **Not data**: dictionaries, thresholds and mappings the scripts read go in `config/` (see [`../extensible-dictionary.md`](../extensible-dictionary.md)).
- **Not output formats**: text a human may want to reword (pages, briefs, reports) lives in `references/templates/` with `{{PLACEHOLDER}}` slots; the script fills it and lists the placeholders in `--help` (see [`../output-template.md`](../output-template.md)). Only machine contracts (JSON keys, frontmatter fields a script reads back) stay in code.

## 2. Layout and naming

```text
scripts/
├── {skill}.sh            # Optional entry point: setup (venv, deps, compiled helpers), --test, exec orchestrator
├── {use_case}.py         # Optional orchestrator: sequence, loops, conditions, checks, report, exit codes
├── {domain}_lib.py       # Atomic utils shared by the scripts of this skill (one action per function)
├── {action}.py           # Single-purpose script (a util or a gate) when it is run on its own
├── _fixture.py           # Optional shared test fixture (temp vault, sample files)
├── test_{script}.py      # One test file per script, next to it
└── requirements.txt      # Only if there are non-stdlib dependencies
```

| Rule | Why |
| --- | --- |
| Python files are `snake_case.py` | Hyphens can't be imported, so the util can't be reused or tested by import |
| The entry point is `{skill}.sh`, named after the skill | One obvious command for humans; `SKILL.md` names only this path |
| Tests are `test_{script}.py`, next to the script | `unittest discover -p 'test_*.py'` finds them; the owner is obvious |
| Private helpers start with `_` | Not part of the CLI; don't document them in `usage.md` |

## 3. Layers

- **Atomic utils**: one action each, inputs → output. No prompts, no global state, no decision about *which* files to touch. Raise an error instead of printing and exiting. Pure (text in, text out) where possible.
- **Orchestrator** (optional, one per use case): owns the control flow: discovery, `for` loops, conditions, idempotency checks, `--dry-run`, per-item status, summary, exit code. It calls utils and holds **no** transformation logic.
- **Entry point** (optional): owns setup only, then `exec`s the orchestrator with `"$@"`.
- **Who sequences?** If no judgement is needed between steps, an orchestrator script does it. If agent judgement sits between steps (writing pages, reviewing a plan), `SKILL.md` sequences the scripts and each script is a **gate** (validate, check, fail with exit 1 and a list of findings). Exemplar: `second-brain-ingest-advanced` (`init_run.py` → agent work → `validate_plan.py`, `check_links.py`, `check_scope.py`).

## 4. Interface — operable by agent or human

- **`--help` is the first documentation.** Use `argparse` with the module docstring as the description (`description=__doc__`, `RawDescriptionHelpFormatter`), so `--help` shows usage, inputs, outputs, statuses and exit codes. It exits 0.
- **Non-interactive.** All input comes from arguments, env vars or stdin. Never prompt: the agent asks the user, then passes a flag.
- **stdout = results, stderr = progress and warnings.** Readable text by default for humans; `--json` when an agent branches on the result.
- **Fixed status vocabulary** per item (e.g. `written`, `skipped-up-to-date`, `locked`, `error`), listed in `--help` or `usage.md`, so `SKILL.md` can map each status to a follow-up.
- **Exit codes are documented.** `0` = success. Non-zero = a gate failed, an item failed, or bad arguments; say which code means what.
- **Safe by default.** Any script that writes supports `--dry-run`, re-running is idempotent (skip what's up to date), and it never overwrites a file it didn't create without `--force`. Writes are atomic (temp file + rename).
- **Secrets** (passwords, tokens, API keys) follow [`../secret-configuration.md`](../secret-configuration.md): always read from the env var `{SKILL}_{THING}`; optionally pre-filled from `~/.config/{skill}/.env` by the entry point (keys illustrated in `references/.env.example`); a human can override explicitly with a script parameter or by stating the value to the agent. Never guessed, never prompted, never printed.

## 5. Paths, environment, dependencies

- Resolve the skill's own files relative to the script (`Path(__file__).resolve().parent`), never the current directory. No hard-coded user paths; docs use `<skills-dir>`.
- Env vars are named `{SKILL}_{THING}` (e.g. `PDF_EXTRACT_VENV`), listed in `--help` or `usage.md`, and registered in [`../../README.md`](../../README.md) → *Environment Variables*.
- Prefer the **Python 3 standard library**. Non-stdlib deps go in `requirements.txt`, installed by the entry point into a private venv at `~/.cache/{skill}/venv`, never into the user's global Python. Details: [`python.md`](./python.md) §1 and [`bash.md`](./bash.md) §3.
- Runtime state (venv, compiled helpers, logs) goes under `~/.cache/{skill}/`, never into the skill folder.
- Shell is for setup and glue; logic that needs tests goes in Python.

Language conventions: **Python** → [`python.md`](./python.md) (file layout, style, `parse_args`/`main`, tests). **Bash** → [`bash.md`](./bash.md) (entry point template, venv bootstrap, how to call Python, portability).

## 6. Reuse between skills

- A util another skill needs stays with its **owner**. The other skill points to it by skill name + path and says that skill must be linked (README reuse option 4).
- Copy only when the script must run without the other skill installed, with a header `# Copied from {skill}/{path} — keep in sync`. Known drift: see AGENTS.md *Known debt*.

## 7. Tests

- One `test_{script}.py` per script, stdlib `unittest`. Run with `python3 -m unittest discover -s scripts -p 'test_*.py'`, or `{skill}.sh --test` when there's an entry point.
- Work in temp dirs; no network; no real user data. Slow or platform-specific tests (OCR, audio) are opt-in through an env var.
- Test every shipped `config/` file (it parses, it has the expected shape).

## 8. Documentation and `SKILL.md`

- `references/usage.md` only when `--help` isn't enough: output format, statuses, env vars, reuse as a library. Two entry points: *Quick start / Options* for humans, *Agent contract* for agents.
- `SKILL.md` calls `<skills-dir>/{skill}/scripts/{entry}` and never re-describes the algorithm. It says *"don't read the sources to run the skill; `--help` and `references/usage.md` are enough"*, and maps each status to a follow-up.
- The optional `allowed-tools` hint can scope shell access to the entry point (e.g. `Bash(*{skill}/scripts/{skill}.sh*)`).

## 9. Verify (adds to `../skill-factory.md` step 7)

- [ ] All tests pass.
- [ ] Every runnable script: `--help` exits 0 and describes inputs, options, outputs, exit codes.
- [ ] Any script that writes: `--dry-run` writes nothing; a second run is a no-op.
- [ ] No prompts; no hard-coded user paths; secrets per [`../secret-configuration.md`](../secret-configuration.md) (env var, optional `.env`, `references/.env.example`, explicit override).
- [ ] `SKILL.md` names the entry point (or the gates in order) and handles every status.

## Known gaps in existing skills

Fix these when you next touch the skill, not as a drive-by:

- `lint-unformat/scripts/`: hyphenated file names (`align-tables.py`, `fix-table-wikilinks.py`, `relink-wiki.py`) can't be imported; no `usage.md`, no single entry point.
- `second-brain-ingest-advanced/scripts/`: usage lives in each docstring, but `--help` shows bare `argparse` output because the docstring isn't wired in as `description`.
