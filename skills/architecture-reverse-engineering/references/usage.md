# architecture-reverse-engineering — usage reference (humans & AI agents)

Two read-only scripts behind one entry point:

- **`scan`** collects the evidence: which files exist, which external touchpoints the code and config show, and the runtime specs.
- **`check`** is the gate on the document the agent (or you) wrote from `references/templates/component-diagram.md`.

Drawing the diagram is judgement and is not scripted. Humans read [Quick start](#quick-start) and [Options](#options); agents read [Agent contract](#agent-contract).

## Quick start

```bash
S=<skills-dir>/architecture-reverse-engineering/scripts

$S/architecture-reverse-engineering.sh scan ~/code/orders-service              # readable report
$S/architecture-reverse-engineering.sh scan ~/code/orders-service --json       # for agents / jq
$S/architecture-reverse-engineering.sh scan . --bucket middleware --tier confident
$S/architecture-reverse-engineering.sh check docs/architecture/component-diagram.md --repo .
$S/architecture-reverse-engineering.sh --test                                   # unit tests
```

Stdlib-only Python 3.9+: no venv, nothing to install. Nothing is ever written: `scan` prints to stdout, `check` only reads.

## Options

### `scan <repo>`

| Option | Default | Effect |
| --- | --- | --- |
| `--json` | off | JSON report on stdout; progress on stderr |
| `--bucket B` | all | Only these buckets (repeatable): `upstream`, `downstream-peer`, `downstream-cloud`, `middleware`, `auth`, `cross-cutting`, `inferred-clue` |
| `--tier confident\|flag` | both | Only one tier |
| `--max-hits N` | `60` | Hits kept per category, confident and most-cited first. `0` = no cap. Dropped counts are in `summary.truncated` |
| `--signals FILE` | `config/signals.json` | Replace the shipped signals |
| `--signals-local FILE` | see below | Local overlay merged on top of the signals |
| `--no-local` | off | Ignore any local overlay |
| `-q`, `--quiet` | off | Summary line only (text mode) |

### `check <doc.md>`

| Option | Default | Effect |
| --- | --- | --- |
| `--repo ROOT` | none | Also check that every backticked path in the doc exists in the repo |
| `--template FILE` | `references/templates/component-diagram.md` | Template whose `##` headings are required |
| `--json` | off | JSON findings on stdout |

### Environment variables

| Variable | Default | Purpose |
| --- | --- | --- |
| `ARCHITECTURE_REVERSE_ENGINEERING_SIGNALS_LOCAL` | `~/.config/architecture-reverse-engineering/signals.local.json` (used only if it exists) | Local signals overlay |
| `ARCHITECTURE_REVERSE_ENGINEERING_PYTHON` | `python3` | Interpreter used by the entry point |

## Signals: shipped set + local overlay

`config/signals.json` is the committed, **generic** set: public libraries, SDKs, file conventions. It documents itself in its `rules` block (file kinds, inventory, categories with `patterns` = confident tier and `flag_patterns` = flag tier, `known_noise`, `runtime_specs`, `secret_key_regex`).

Patterns that name your organisation's internal clients, hosts or platforms must **not** go there. Put them in the local overlay, which has the same shape and only the keys you add to:

```json
{
  "categories": {
    "internal-platform": {
      "bucket": "downstream-peer",
      "scopes": ["source", "config"],
      "patterns": ["\\bacme-platform-client\\b", "platform\\.acme\\.internal"]
    },
    "cache": { "patterns": ["\\bacme-kv\\b"] }
  },
  "known_noise": [{ "path": "legacy/*" }]
}
```

Merge rule: lists are appended, categories merged by name (a new category needs a `bucket`), scalars replace. The report's `signals` field lists the files used.

## What the scan never does

- Read `.env`, key stores or certificates (`skip_files`), or descend into build output and vendored code (`skip_dirs`).
- Print a secret value: on any `key: value` / `key=value` line whose key matches `secret_key_regex`, the value is replaced by `<redacted>` (placeholders like `${DB_PASSWORD}` are kept).
- Follow symlinks or read files over `max_file_bytes`.

## Agent contract

### `scan --json`

```json
{
  "repo": "/abs/path",
  "signals": ["/abs/config/signals.json", "/abs/signals.local.json"],
  "summary": {
    "files_scanned": 150,
    "files_by_kind": {"source": 90, "config": 20, "...": 0},
    "files_skipped": {"binary": 0, "too-large": 0, "unknown-kind": 12, "unreadable": 0},
    "hits": 60,
    "hits_by_tier": {"confident": 47, "flag": 13},
    "hits_by_bucket": {"upstream": 10, "...": 0},
    "truncated": {"database": 45}
  },
  "inventory": [{"path": "build.gradle.kts", "kind": "manifest", "reveals": "..."}],
  "runtime_specs": [{"spec": "base-image", "value": "zulu-openjdk:21-jre", "path": "Dockerfile", "line": 1}],
  "hits": [{"bucket": "middleware", "category": "queue", "tier": "confident",
            "path": "src/main/resources/application.yml", "match": "kafka",
            "lines": [12, 14], "snippet": "kafka:"}]
}
```

- One hit per (category, tier, matched text) per file, with every line number. Sorted by bucket, then category, confident first.
- `tier`: `confident` = evidence; `flag` = a lead to judge (see `references/classification.md`).
- Exit codes: `0` scan done (even with no hits), `1` repo is not a directory or the signals/overlay file is missing or invalid, `2` bad arguments.

### `check --json`

```json
{"doc": "docs/architecture/component-diagram.md", "ok": false,
 "findings": [{"code": "UNQUOTED_CHARS", "line": 14, "message": "label of api has brackets; wrap it in double quotes"}]}
```

| Code | Fix |
| --- | --- |
| `MISSING_SECTION` | Add the `##` section the template requires (or change the template) |
| `NO_MERMAID` | Add the diagram as a ```` ```mermaid ```` block |
| `UNBALANCED` | Close every `subgraph` with `end` |
| `DUP_ID` | Give each node one id and one label; reuse the bare id in later edges |
| `UNQUOTED_CHARS` | Wrap the label in double quotes: `id["Label (x)"]` |
| `UNKNOWN_CLASS` | Add the `classDef` or fix the class name |
| `MISSING_EVIDENCE` | Fix the cited path, or drop the citation if it was a guess |

Line numbers are lines of the doc (`0` = whole document). Exit codes: `0` no findings, `1` findings, `2` bad arguments or an unreadable doc/template/repo.
