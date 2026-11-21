---
name: architecture-reverse-engineering
description: >
  Reverse-engineer an existing codebase into an evidence-backed architecture
  component diagram: upstream callers, downstream peer services and cloud
  dependencies (with auth), owned middleware (database, cache, queue, storage,
  search), runtime specs (language, framework, base image, key libs) and
  components inferred from clues, each citing the files that prove it. A
  read-only script scans the repo for evidence; the agent classifies, draws the
  Mermaid diagram from a template, and a gate script checks it. Writes
  {repo}/docs/architecture/component-diagram.md. Use when the user says "build
  the architecture diagram for this repo", "reverse-engineer the architecture",
  "component diagram of this service", "map the dependencies of this service",
  "what does this service talk to", or is onboarding onto an unknown codebase.
  To draw a diagram from a description, or convert an image/ASCII diagram, use
  /diagram-architecture instead.
allowed-tools: Bash(*architecture-reverse-engineering/scripts/architecture-reverse-engineering.sh*) Read Glob Grep Write
version: 0.2.0
---

# Architecture Reverse Engineering

Turn a repository into one Markdown document: a component diagram where every box is backed by a file, and every guess is marked as one. Good output is **scannable** (tables, short lines), **honest** ("unknown, but something exists here" is a valid row) and **checkable** (a reader can open the cited file).

The scripts collect evidence and check the result; the agent does the judgement in between. Never modify the repo's source files. Never commit unless asked.

## Files

| File | Load when |
| --- | --- |
| `scripts/architecture-reverse-engineering.sh` | Always: the single entry point (`scan`, `check`, `--test`). Stdlib Python, nothing to install |
| `references/classification.md` | Step 3: how to turn scan hits into components, layers, auth and confidence |
| `references/templates/component-diagram.md` | Step 4: the output skeleton and per-section guidance. Read it before writing |
| `diagram-architecture/references/mermaid-patterns.md` | Step 4, only if you need Mermaid syntax help (owned by `/diagram-architecture`, which must be linked) |
| `references/usage.md` | When you need an option not listed here, the JSON fields, the overlay format, or a finding code's fix |
| `config/signals.json` | Step 6 only: to add a pattern (write-back). Never needed to run the scan |

Don't read the Python sources to run the skill: `--help` and `references/usage.md` are enough.

## Output

| Template | Use when |
| --- | --- |
| `references/templates/component-diagram.md` | Always: the one document this skill writes, at `{repo}/docs/architecture/component-diagram.md` (create `docs/architecture/` if missing) |

The template owns the sections, the diagram conventions and the self-review. To change the format, edit the template; `check` follows it.

## Process

1. **Resolve the repo.** Default: the current working directory's repo root. Ask once only if it's ambiguous (a monorepo with several services: which one?). If the output file already exists, read it: you are refreshing it, keep any hand-written notes the user wants kept.

2. **Scan for evidence.**

   ```bash
   <skills-dir>/architecture-reverse-engineering/scripts/architecture-reverse-engineering.sh scan "<repo>" --json
   ```

   - Exit `1`: the path isn't a directory or the signals file is invalid; report the stderr line and stop.
   - Read `inventory` first, then open the manifests, the main config file, the Dockerfile and the README it lists.
   - If `summary.truncated` cuts a bucket you need, re-run with `--bucket <b> --max-hits 0`.

3. **Classify and infer.** Load `references/classification.md`. Merge hits into components, decide direction (upstream / downstream), owned vs shared, auth per edge, and confidence. Open the cited lines to confirm; `flag` hits are leads, not evidence. Then do the **manual sweep** it describes (package tree + main config): the scan only knows its patterns.

4. **Write the document.** Read `references/templates/component-diagram.md` and fill it. Every component cites at least one repo-relative path in backticks. Inferred components are ⚠, styled `inferred`, and listed with clue + confidence. No secret values.

5. **Gate.**

   ```bash
   <skills-dir>/architecture-reverse-engineering/scripts/architecture-reverse-engineering.sh check "<repo>/docs/architecture/component-diagram.md" --repo "<repo>" --json
   ```

   Exit `1`: fix every finding (`references/usage.md` → *Agent contract* lists the fix per code) and re-run until exit `0`. Exit `2`: the doc or repo path is wrong.

6. **Grow the signals — every time, without being asked.** Each touchpoint the manual sweep found that the scan missed, and each confident hit that turned out to be noise, becomes one write in the same turn:

   | You found | Write | Where |
   | --- | --- | --- |
   | A public library, SDK or file convention the scan missed | Add a regex to `categories.{category}.patterns` (or a new category with its `bucket`) | `config/signals.json` (shipped, generic) |
   | A generic word that only sometimes means a touchpoint | `flag_patterns` of that category | `config/signals.json` |
   | A confident hit that is always noise | A `known_noise` entry (`match`, optional `path`, `category`) | `config/signals.json` if generic, else the overlay |
   | An internal client, host or platform name of the user's organisation | Any of the above | The local overlay (`~/.config/architecture-reverse-engineering/signals.local.json`, format in `references/usage.md`). Never in the shipped file |
   | A new place where a runtime spec lives | A `runtime_specs` extractor | `config/signals.json` |

   Then re-run the scan to confirm the new entry matches, run `--test` if you changed the shipped file, and tell the user one line per entry.

7. **Report.** Give the user the file path, the component count by layer, the ⚠ inferred components with their confidence, and any open question that would raise a confidence (a repo to check, an owner to ask). Don't paste the whole document.

## Rules

- **Read-only on the repo**, except for the one output file. Scripts never write.
- **Evidence or ⚠.** No component without a cited file; no guess without the ⚠ mark and a confidence.
- **Secrets stay out.** The scan skips `.env` and key files and redacts secret values; when you open files yourself, name keys and mechanisms, never values.
- **Generic skill, specific overlay.** Organisation-specific names go in the local overlay, never in `config/signals.json`, the template or this file.
- **Syntax is owned elsewhere.** For Mermaid syntax, read `/diagram-architecture`'s reference; don't copy it here.

## Without an agent

A human can run the same evidence scan and gate: `architecture-reverse-engineering.sh scan <repo>` prints a readable report grouped by bucket, and `check <doc> --repo <repo>` validates a hand-written diagram against the template. The signals are then used as-is, never grown.

## Chaining

- `/diagram-architecture`: alternative views (sequence diagram of one flow, C4 context) from the same document.
- `/change-management-1-stage`: stage the generated document if the user wants it committed.
