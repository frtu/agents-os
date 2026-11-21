---
concept: script-layering
summary: Put every deterministic step of a skill in scripts/ as reusable atomic utils, compose them in an optional use-case orchestrator that owns the loops, conditions and checks, and make each script operable by an agent or a human through --help (plus references/usage.md when needed).
exemplars: [transcribe-pdf, second-brain-ingest-advanced, lint-unformat]
related: [extensible-dictionary, output-template]
---

# Script layering

## Problem

A skill whose job is partly mechanical (parse, convert, check, rename, count) leaves that work as prose in `SKILL.md`. The symptoms:

- The agent redoes the same mechanical steps by hand on every run, spending tokens, and gets them slightly different each time.
- `SKILL.md` grows `for each file… if… else…` paragraphs that are really a program written in English.
- One big script does everything: no piece can be reused by another skill or tested alone.
- Only the agent can run the skill. A human who wants the same result has to read the Python source, or ask an agent.

## Pattern

Split deterministic work into **three layers** and keep judgement in `SKILL.md`. **Atomic utils** are small, pure functions or single-purpose scripts: one action each, no orchestration, each with a test. An optional **orchestrator** (one per use case) is the deterministic sequence: discovery, `for` loops, skip/overwrite decisions, checks, error handling, and a summary report with exit codes. An optional **entry point** wraps the orchestrator with setup (venv, dependencies, `--test`). Every runnable script explains itself through `--help`; `references/usage.md` covers what `--help` can't (output format, statuses, agent contract, env vars, reuse). `SKILL.md` then **calls** the entry point and only decides what scripts can't: which inputs, which options the user asked for, how to report, and what to do on failure.

```text
skill-name/
├── SKILL.md                  # Judgement only: resolve inputs → run entry point → read report → follow up
├── references/
│   └── usage.md              # Optional: humans (quick start, options) + agents (contract: --json, statuses)
└── scripts/
    ├── {skill}.sh            # Optional entry point: bootstrap (venv, deps), --test, exec orchestrator
    ├── {use_case}.py         # Optional orchestrator: sequence, loops, conditions, checks, report, exit codes
    ├── {domain}_lib.py       # Atomic utils: one action per function, no I/O policy, reusable by other skills
    └── test_*.py             # One test file per script
```

## Use when / Don't use when

| Use when | Don't use when |
| --- | --- |
| A step gives the same output for the same input (no judgement) | The step needs reading comprehension, taste or a decision only the user can make: keep it in `SKILL.md` |
| The same steps run in a fixed sequence, over many files or with skip/retry rules | It is a one-off, single-command step: a shell one-liner in `SKILL.md` is enough |
| A human should be able to get the result without an agent | The data, not the code, grows with use: pick [`extensible-dictionary.md`](../extensible-dictionary.md) (the script reads a JSON the agent grows) |
| Another skill could reuse a piece (a parser, a normaliser) | |

Layers are optional from the top: utils alone are fine; add an orchestrator once there's a sequence with conditions and no judgement in between (otherwise `SKILL.md` sequences the scripts as gates); add an entry point once there's setup. The concrete rules every script follows (naming, `--help`, exit codes, tests) are in [`rules.md`](./rules.md).

## Anatomy

| Part | Rule |
| --- | --- |
| **Atomic util** | One action, inputs → output, no prompts, no global state, no decisions about *which* files. Pure where possible (text in, text out). Has a test. Importable by another skill (via README reuse option 4, *point to the owning skill*) |
| **Orchestrator** | Owns the *control flow*: discovery, loops, conditions, idempotency checks (skip when up to date, never overwrite foreign files without `--force`), `--dry-run`, error capture per item. Calls utils; holds no transformation logic. Ends with a summary and a meaningful exit code |
| **Entry point** | Owns *setup*: environment, dependencies, `--test`. Then hands off to the orchestrator with `"$@"`. The only path `SKILL.md` names |
| **Agent/human contract** | `--help` lists inputs, options, defaults and outputs and exits 0. `--json` (or another stable format) for agents, readable text for humans; progress on stderr, results on stdout. Statuses are a fixed vocabulary the agent can branch on |
| **`references/usage.md`** | Added when `--help` isn't enough. Two entry points: *Quick start / Options* for humans, *Agent contract* for agents. `SKILL.md` says to load it only for options or statuses it doesn't list |
| **`SKILL.md`** | Calls the entry point; never re-describes the algorithm. Says "don't read the sources to run the skill". Maps each status to a follow-up action |

## Exemplar walkthrough

**`transcribe-pdf`** (all three layers):

- Atomic utils: `transcribe-pdf/scripts/pdf_lib.py` — `file_sha256`, `write_text_atomic`, `is_up_to_date`, `open_pdf`, `extract_page_text`, `ocr_pages`, `render_markdown`… each one action, tested in `test_pdf_lib.py`.
- Orchestrator: `transcribe-pdf/scripts/pdf_to_md.py` — its docstring states it is "high-level only: discovery, loops, skip/overwrite decisions, choosing when to call OCR, reporting". The decision flow is written as a table in the docstring, and exit codes are documented (0 / 1 / 2). Tested in `test_pdf_to_md.py`.
- Entry point: `transcribe-pdf/scripts/transcribe-pdf.sh` — creates a venv, reinstalls when `requirements.txt` changes, runs `--test`, then `exec`s the orchestrator.
- Contract: `transcribe-pdf/references/usage.md` — *Quick start* and *Options* for humans, *Agent contract* for agents (`--json`, statuses), plus *Reusing the library from another skill*.
- `SKILL.md` only resolves inputs, runs the entry point with `--json`, reports counts by status and maps `locked` / `written-empty` / `skipped-foreign` to follow-ups.

What makes it succeed: re-running is safe (SHA-256 idempotency lives in the orchestrator, not in the agent's memory), and a human gets the same result from the same command.

**`second-brain-ingest-advanced`** (utils + gates, sequenced by `SKILL.md`): `wikilib.py` holds the shared atomic helpers; `init_run.py`, `validate_plan.py`, `check_links.py`, `check_scope.py`, `render_briefs.py`, `build_portal_log.py` are single-purpose steps, each with a test and a shared `_fixture.py`. There's no orchestrator script because agent work sits between the steps, so `SKILL.md` runs them in order and each check is a **gate** that exits 1 with findings.

**`lint-unformat`** (utils + light orchestrator): `normalize_image_links.py` and `normalize_whitespaces.py` are atomic normalisers; `normalize_markdown.py` imports them and applies them independently or in sequence, with `argparse` `--help`. Gap to close if you touch it: no `references/usage.md` and no single entry point.

## Adoption checklist

1. List the skill's steps. Mark each one **deterministic** (same input → same output) or **judgement**.
2. For each deterministic step, write an atomic util (function in `{domain}_lib.py` or a small script) and its test. Check the catalog first: if another skill owns that util, link to it instead of copying.
3. If the deterministic steps run in sequence with loops or conditions, write an orchestrator: discovery, idempotency checks, `--dry-run`, per-item status, summary, exit codes.
4. If there's setup (dependencies, a compiled helper), add an entry point that bootstraps, supports `--test`, and hands off to the orchestrator.
5. Give every runnable script `--help`. Add `--json` and a fixed status vocabulary if an agent branches on the result.
6. Write `references/usage.md` if `--help` doesn't cover output format, statuses, env vars or reuse.
7. Rewrite `SKILL.md` to call the entry point and handle statuses. Delete the prose that described the algorithm.
8. Verify: tests pass; `--help` exits 0; a human can follow `usage.md` without reading the sources.

## Anti-patterns

- **Program in prose**: `SKILL.md` spells out loops and conditions the agent executes by hand. Move them into the orchestrator.
- **God script**: one file mixes discovery, transforms and reporting. Nothing can be reused or tested alone.
- **Orchestrator with logic inside**: regexes and parsing in the orchestrator instead of in utils. They drift from the tested library.
- **Agent-only contract**: output is only JSON with no human-readable mode, or behaviour is only documented in `SKILL.md`. A human can't operate it.
- **Silent side effects**: overwrites without `--force`, no `--dry-run`, no exit code. The agent can't tell success from failure.
- **Copied utils**: the same helper pasted into two skills (see the `relink-wiki.py` drift in AGENTS.md *Known debt*). Give it one owner.
