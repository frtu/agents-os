# Skill factory — Bash script conventions

**Load in write mode** when you write or change a `.sh` file in a skill's `scripts/`, typically the **entry point** that sets things up and launches Python. General `scripts/` rules are in [`rules.md`](./rules.md); Python conventions (`requirements.txt`, venv contents, `main(argv)`) are in [`python.md`](./python.md). Reference implementation: `pdf-extract/scripts/pdf-extract.sh`.

## 1. Role of shell in a skill

- Shell is for **setup and glue**: find the skill's folder, create the venv, check that a binary exists, run the tests, `exec` the Python orchestrator.
- **Logic goes in Python**: loops over files, parsing, decisions, reporting. Anything that needs a test is Python.
- One entry point per skill, named `{skill}.sh`. `SKILL.md`, `usage.md` and humans call only this path.

## 2. File layout

```bash
#!/bin/bash
# {skill}.sh — entry point. {One line: what it sets up, what it runs.}
#
# Usage:
#   {skill}.sh <inputs> [...] [options]     # options: see `{skill}.sh --help`
#   {skill}.sh --test                        # run the unit tests
#
# Env:
#   {SKILL}_VENV      venv location   (default ~/.cache/{skill}/venv)
#   {SKILL}_CACHE     cache location  (default ~/.cache/{skill})
#   {SKILL}_PYTHON    base interpreter used to create the venv (default python3)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(dirname "$SCRIPT_DIR")"                       # only if you need references/ or config/
VENV="${MY_SKILL_VENV:-$HOME/.cache/my-skill/venv}"         # my-skill / MY_SKILL = the skill name
PY_BASE="${MY_SKILL_PYTHON:-python3}"
REQ="$SCRIPT_DIR/requirements.txt"
STAMP="$VENV/.requirements.sha"
```

- **Header comment** = the shell's `--help`: usage lines and every env var with its default. Keep it in sync with `usage.md`.
- **`set -euo pipefail`** right after the header.
- **`SCRIPT_DIR` from `BASH_SOURCE[0]`**, resolved with `cd … && pwd`. It works through the `<skills-dir>` symlink and from any current directory. Never rely on `$PWD`.
- **Every tunable is an env var with a default** (`${VAR:-default}`), named `{SKILL}_{THING}`, under `~/.cache/{skill}/`. Register them in the library README → *Environment Variables*.

## 3. Calling Python

### Stdlib-only scripts

```bash
exec python3 "$SCRIPT_DIR/{use_case}.py" "$@"
```

No venv needed. A separate entry point is optional: `SKILL.md` can call `python3 <skills-dir>/{skill}/scripts/{script}.py` directly.

### Scripts with `requirements.txt` — private venv in `~/.cache/{skill}/venv`

```bash
ensure_venv() {
    local want
    want="$(shasum -a 256 "$REQ" | cut -d' ' -f1)"
    if [ ! -x "$VENV/bin/python" ]; then
        echo "{skill}: creating venv in $VENV" >&2
        mkdir -p "$(dirname "$VENV")"
        "$PY_BASE" -m venv "$VENV"
    fi
    if [ ! -f "$STAMP" ] || [ "$(cat "$STAMP")" != "$want" ]; then
        echo "{skill}: installing requirements" >&2
        "$VENV/bin/python" -m pip install -q --disable-pip-version-check \
            --only-binary=:all: -r "$REQ" >&2
        echo "$want" > "$STAMP"
    fi
}

ensure_venv

if [ "${1:-}" = "--test" ]; then
    cd "$SCRIPT_DIR"
    exec "$VENV/bin/python" -m unittest discover -s "$SCRIPT_DIR" -p 'test_*.py' -v
fi

exec "$VENV/bin/python" "$SCRIPT_DIR/{use_case}.py" "$@"
```

Rules this encodes:

| Rule | Why |
| --- | --- |
| Venv in `~/.cache/{skill}/venv`, never in the skill folder | The skill folder is version-controlled and symlinked; the cache is per-machine and disposable |
| Call `"$VENV/bin/python"` directly; never `source activate` | No shell state leaks; works the same from an agent, cron or a human shell |
| Reinstall when the SHA-256 of `requirements.txt` changes (stamp file in the venv) | Updating a dependency is just editing `requirements.txt`; unchanged runs skip pip entirely |
| `--only-binary=:all:` | No compiler or Rust toolchain needed on the user's machine |
| `-q --disable-pip-version-check`, pip output to stderr | stdout stays clean for the Python report (`--json`) |
| Setup messages to stderr, prefixed `{skill}:` | A human sees what's happening; an agent parsing stdout isn't disturbed |
| `--test` runs with the venv's Python | Tests import the same packages as the real run |
| `exec` the final command, with `"$@"` | The Python exit code and signals pass straight through; every option reaches `argparse` untouched |
| Options are parsed by Python, not by the shell | One parser, one `--help`. The shell only intercepts `--test` (and other setup-only flags) |

To reset: delete `~/.cache/{skill}/venv`; the next run recreates it.

### Secrets and `.env`

Secrets follow [`../secret-configuration.md`](../secret-configuration.md): always an env var, optionally pre-filled from a `.env` file, explicit override on top. When the skill supports the optional `.env`, the entry point loads `~/.config/{skill}/.env` **before** calling Python, so the script itself only reads env vars. Ship the keys as `references/.env.example` (placeholders only):

```bash
ENV_FILE="${MY_SKILL_ENV_FILE:-$HOME/.config/my-skill/.env}"

# Load MY_SKILL_* keys from the .env file. A variable already set in the shell wins.
load_env_file() {
    local file="$1" line key val
    [ -f "$file" ] || return 0
    while IFS= read -r line || [ -n "$line" ]; do
        case "$line" in ''|'#'*) continue ;; esac
        line="${line#export }"
        key="${line%%=*}"
        val="${line#*=}"
        case "$key" in MY_SKILL_*) ;; *) continue ;; esac     # only this skill's keys
        case "$key" in *[!A-Za-z0-9_]*) continue ;; esac      # valid names only
        val="${val%\"}"; val="${val#\"}"; val="${val%\'}"; val="${val#\'}"
        case "$val" in "~/"*) val="$HOME/${val#\~/}" ;; esac    # expand a leading ~/
        if [ -z "${!key+x}" ]; then export "$key=$val"; fi
    done < "$file"
}

load_env_file "$ENV_FILE"
```

- **Load it first**: right after `SCRIPT_DIR`, before any other `${VAR:-default}` setting, so `.env` can also set those (`{SKILL}_VENV`, …).
- **Parse, don't `source`**: the file is read as `KEY=VALUE` lines, so a stray command in it never runs.
- **A leading `~/` is expanded** to `$HOME/`; nothing else is (no `$VAR`, no command substitution).
- **Only the skill's own prefix** is loaded, so one skill's `.env` can't change another tool's settings.
- **The shell wins**: a variable already exported (a human's one-off `MY_SKILL_PASSWORD=… ./my-skill.sh`) is not overwritten.
- The file lives in `~/.config/{skill}/` (persistent, per user), not in `~/.cache/` (disposable) and never in the skill folder. Create it with `chmod 600`.

### Python packages (`python -m`)

When the scripts are packages (`scripts/{pkg}/__main__.py`), set the path once and call the module:

```bash
export PYTHONPATH="$SCRIPT_DIR:${PYTHONPATH:-}"
exec "$PYTHON" -m {pkg} "$@"
```

Exemplar: `transcribe-voice-memo/scripts/transcribe.sh`.

## 4. Coding conventions

- **Portable to macOS's default `/bin/bash` 3.2**: no associative arrays (`declare -A`), no `mapfile`/`readarray`, no `${var,,}`. Use `#!/bin/bash`.
- **Portable commands**: `shasum -a 256` (present on macOS and most Linux distributions), `mkdir -p`, `cd … && pwd`. Avoid GNU-only flags (`sed -i` without a suffix, `readlink -f`).
- **Quote every expansion**: `"$VAR"`, `"$@"`, `"$(cmd)"`. Use `${1:-}` for optional arguments under `set -u`.
- **Functions** in `snake_case`, declared before use, with `local` variables. Constants and env-derived settings in `UPPER_SNAKE` at the top.
- **Errors**: print `{skill}: <what failed> — <what to do>` to stderr and `exit 1`. Check required binaries with `command -v tool >/dev/null || { echo "{skill}: tool not found — install with …" >&2; exit 1; }`.
- **Don't `cd`**, except right before an `exec` that needs it (tests). Pass absolute paths instead.
- **Secrets**: never put one on a command line the script builds, echoes or logs. Pass it through the environment (the entry point loads `.env`, see §3).
- **No interactive prompts** (`read`): an agent can't answer them. Take flags or env vars.
- Lint with `shellcheck` when it's available.

## 5. How `SKILL.md` calls it

```bash
<skills-dir>/{skill}/scripts/{skill}.sh "<path>" [options] --json
```

- `SKILL.md` names the entry point and the options it may pass. It says not to read the sources to run the skill.
- The optional `allowed-tools` hint can scope shell access to the entry point: `Bash(*{skill}/scripts/{skill}.sh*)`.
- Humans run the same command; `usage.md` gives a `S=<skills-dir>/{skill}/scripts` shortcut for quick-start examples.

## 6. Checklist

- [ ] Header with usage + env vars; `set -euo pipefail`; `SCRIPT_DIR` from `BASH_SOURCE[0]`.
- [ ] Venv (if any) in `~/.cache/{skill}/venv`, reinstalled on `requirements.txt` change, `--only-binary=:all:`.
- [ ] Setup output on stderr; final command `exec … "$@"`.
- [ ] `--test` runs the tests with the same interpreter.
- [ ] Bash 3.2 compatible, every expansion quoted, no prompts.
- [ ] Secrets: optional `.env` loaded from `~/.config/{skill}/.env` (prefix-filtered, shell wins), `references/.env.example` shipped, never echoed.
- [ ] Runs the same from any current directory, through the `<skills-dir>` symlink.
