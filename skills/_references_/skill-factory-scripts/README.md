# Skill factory — scripts

Rules and design concept for a skill's **`scripts/` folder**: deterministic work, reusable atomic utils, optional use-case orchestrators, and scripts that an agent **or** a human can operate.

**Load in write mode** when the skill has, or should have, `scripts/`. Optional in read mode. Start with [`../skill-factory.md`](../skill-factory.md) (the general process); it sends you here at step 3.

| File | Kind | Load when |
| --- | --- | --- |
| [`rules.md`](./rules.md) | Rules | Always, when writing or changing a script: what goes in `scripts/`, layout & naming, layers, interface (`--help`, `--json`, exit codes, `--dry-run`), paths & deps, reuse, tests, `usage.md`, verify checklist |
| [`python.md`](./python.md) | Conventions | Writing or changing a `.py`: dependencies & `~/.cache/{skill}/venv`, `requirements.txt`, file layout, code style, `parse_args`/`main(argv)`, tests |
| [`bash.md`](./bash.md) | Conventions | Writing or changing a `.sh` (usually the entry point): template, venv bootstrap, how to call Python (`exec "$VENV/bin/python" … "$@"`), `--test`, bash 3.2 portability |
| [`script-layering.md`](./script-layering.md) | Concept | Designing the scripts of a new skill, or the agent keeps redoing mechanical steps by hand: the why, the exemplar walkthrough (`transcribe-pdf`, `second-brain-ingest-advanced`, `lint-unformat`) and the adoption checklist |

Summary (details in `rules.md`):

1. Deterministic → `scripts/`; judgement → `SKILL.md`; data → `config/`.
2. **Atomic utils** (reusable, tested) → optional **orchestrator** (loops, conditions, checks) → optional **entry point** (setup).
3. Every script: `--help`, non-interactive, results on stdout, documented exit codes, `--dry-run` if it writes. `references/usage.md` when `--help` isn't enough.
4. Python: stdlib first; otherwise `requirements.txt` in a private venv at `~/.cache/{skill}/venv`. Bash: the entry point bootstraps the venv and `exec`s Python with `"$@"`.
