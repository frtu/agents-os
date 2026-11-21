---
concept: secret-configuration
summary: A skill reads every secret from an environment variable, optionally pre-filled from a private .env file (illustrated by references/.env.example), and lets a human override it explicitly, by a script parameter or by stating it to the agent, never by the agent guessing.
exemplars: [transcribe-pdf]
related: [script-layering, extensible-dictionary]
---

# Secret configuration

## Problem

A skill needs a password, token or API key, and each script invents its own way to get it. The symptoms:

- The agent types the secret into a command line, so it ends up in the transcript, shell history and logs.
- The agent **guesses**: it tries common passwords, reuses one it saw in another file, or reads the user's dotfiles hoping to find it.
- Every run asks for the secret again, so the user pastes it into the chat each time.
- A real `.env` gets committed next to the skill, or nobody knows which variables a skill expects because only the code says so.
- A human can't do a quick one-off run with a different value without editing a config file.

## Pattern

**One source at runtime: the environment variable** `{SKILL}_{THING}`. The script reads only that (plus an explicit override). Everything else is a way to **fill** that variable. **Optionally**, the entry point pre-fills it from a private `.env` file outside the repo (`~/.config/{skill}/.env`). The skill ships a **`references/.env.example`** with every key and a placeholder value, so humans and agents know what to set without reading code. **Finally**, a human can always **override** the value for one run, explicitly: as a script parameter (`--password …`), or by **telling the agent** the value in the conversation. The agent never guesses, searches for or invents a secret.

```text
skill-name/
├── SKILL.md                    # Which secret, how to ask for it, what the agent must never do
├── references/
│   ├── .env.example            # Every {SKILL}_* key, placeholder values, comments. Committed. Never real values
│   └── usage.md                # Precedence + setup commands for humans
└── scripts/
    ├── {skill}.sh              # Optionally loads ~/.config/{skill}/.env (only {SKILL}_* keys, shell wins)
    └── {use_case}.py           # Reads {SKILL}_{THING}; an explicit --flag overrides it

~/.config/{skill}/.env          # Optional, private (chmod 600), per user, never in the repo
```

Precedence, highest first:

| # | Source | Who sets it | When |
| --- | --- | --- | --- |
| 1 | **Explicit override**: script parameter (`--password …`), or a value the user explicitly gave the agent in the conversation | A human, on purpose | A one-off run with a different value |
| 2 | **Environment variable** `{SKILL}_{THING}` already set in the shell | Human shell, cron, CI, the agent's environment | Always the default source |
| 3 | **`.env` file** `~/.config/{skill}/.env` (optional), loaded into the environment by the entry point only for keys not already set | A human, once | Persistent per-user setup |
| — | Nothing set | — | The script fails with a clear status (e.g. `locked`) naming the variable and pointing to `.env.example`. It never prompts |

## Use when / Don't use when

| Use when | Don't use when |
| --- | --- |
| A script needs a password, token, API key, or any value that must not be committed or logged | The value isn't secret (paths, thresholds, flags): a plain env var with a default or `config/` is enough |
| A skill is run by both humans and agents, or from cron/CI | The value grows with use (word lists, mappings): use [`extensible-dictionary.md`](./extensible-dictionary.md) |
| You want "set it once, every run works" without the agent ever holding the value | The secret is owned by another tool's own config (e.g. `gh auth`, a cloud CLI profile): call that tool and let it handle auth |

## Anatomy

| Part | Rule |
| --- | --- |
| **Environment variable** | Named `{SKILL}_{THING}` (e.g. `TRANSCRIBE_PDF_PASSWORD`). The only place the script reads a secret from, apart from the override. Read once (constants or `main`), never deep inside utils. Registered in the library README → *Environment Variables* |
| **`references/.env.example`** | Committed. Lists every `{SKILL}_*` key the skill reads (secret or not), each with a comment and a **placeholder** (`TRANSCRIBE_PDF_PASSWORD=change-me`). Never a real value. States where the real file goes and its permissions |
| **`.env` file** (optional) | `~/.config/{skill}/.env`, `chmod 600`, created by the human (e.g. `cp references/.env.example ~/.config/{skill}/.env`, then edit). Never in the skill folder or the repo, never in `~/.cache/` (disposable). Path overridable with `{SKILL}_ENV_FILE` |
| **Loader** (entry point) | Parses `KEY=VALUE` lines (never `source`s the file), loads only `{SKILL}_*` keys, never overwrites a variable already set, runs before any other setting is read. Implementation: [`skill-factory-scripts/bash.md`](./skill-factory-scripts/bash.md) §3 *Secrets and `.env`* |
| **Override parameter** | An explicit flag (`--password`, `--token`), documented in `--help` as *explicit override*. It wins over the env var for that run only, and is never persisted |
| **Override by context** | The agent may use a secret **only** if the user explicitly states it in the conversation for this task. It uses it for the run(s) asked, passed inline as the env var for that command (`{SKILL}_{THING}='…' {skill}.sh …`), and does not write it to `.env`, memory, notes or files, or repeat it in its reply |
| **Never guessed** | The agent doesn't try likely values, reuse a secret seen elsewhere, read other files or dotfiles to find one, or ask the user to paste it as a habit. If nothing is set, it reports the status and asks the user to set the env var or `.env` (pointing to `.env.example`), or to give it explicitly |
| **Never echoed** | Scripts don't print, log or include secrets in error messages or JSON reports. The agent doesn't show them in commands it summarises |

## Exemplar walkthrough

**`transcribe-pdf`** (encrypted-PDF password):

- Env var: `TRANSCRIBE_PDF_PASSWORD`, read in `transcribe-pdf/scripts/pdf_to_md.py` `main()` and appended to the passwords tried by `pdf_lib.open_pdf`.
- `.env.example`: `transcribe-pdf/references/.env.example` lists `TRANSCRIBE_PDF_PASSWORD` and the optional path/cache keys with placeholders.
- Optional `.env`: `transcribe-pdf/scripts/transcribe-pdf.sh` `load_env_file` loads `~/.config/transcribe-pdf/.env` (override with `TRANSCRIBE_PDF_ENV_FILE`) before reading any other setting; only `TRANSCRIBE_PDF_*` keys; shell wins. Tested in `test_transcribe_pdf_sh.py` (locked without it, written with it, shell value wins).
- Override parameter: `--password` (repeatable), help text *explicit override*.
- Failure: no working password → status `locked`. `SKILL.md` maps it to "ask the user to set the env var or `.env`, or give it explicitly"; it never guesses.

What makes it succeed: a user sets the `.env` once and every run, agent or human, opens the PDFs, while the agent never holds or prints the password unless the user explicitly hands it over.

## Adoption checklist

1. List every secret the skill needs. Name each env var `{SKILL}_{THING}`.
2. Make the script read only the env var plus an explicit override flag. Read env vars in one place. Never print the value.
3. On a missing or wrong secret, return a clear status or exit code naming the variable. Never prompt.
4. Write `references/.env.example`: every `{SKILL}_*` key, a comment each, placeholder values, where the real file goes (`~/.config/{skill}/.env`, `chmod 600`).
5. If the skill has an entry point, add the `.env` loader ([`skill-factory-scripts/bash.md`](./skill-factory-scripts/bash.md) §3), with a test that the file loads and that a shell value wins.
6. In `SKILL.md`: say which variable holds the secret, and the agent rules (use a value only if the user explicitly gives it, pass it inline for that run, never persist, never guess, never echo).
7. In `usage.md`: the precedence table and the setup commands. Register the env vars in the library README.
8. Verify: `git grep` the skill for anything that looks like a real secret; `.env` and real values are absent from the repo.

## Anti-patterns

- **Secret in a committed file**: a real `.env` or a default password in the skill folder. Commit only `.env.example` with placeholders.
- **Sourcing `.env`**: `source ~/.config/{skill}/.env` runs whatever is in the file. Parse `KEY=VALUE` lines instead.
- **`.env` overwrites the shell**: a stale file silently beats the value a human just exported. The shell wins over the file.
- **Guessing**: the agent tries `1234`, the user's birth year, or a password from another document. Only an explicit statement from the user counts.
- **Persisting an override**: the agent writes a password the user gave once into `.env`, memory or notes. An override is for that run only.
- **Prompting**: `read -s` or `getpass` in a script. Agents can't answer; return a status instead.
- **Leaking in reports**: the secret in an error message, a JSON field or a command the agent echoes back.
- **Many mechanisms**: one script reads a keyring, another a JSON file, a third the env. One runtime source: the env var.
