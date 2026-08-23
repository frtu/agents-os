"""Product Owner persona / system-prompt assembler (spec 002 T010/T011).

Builds the assistant's system prompt from the ratified constitution plus a
curated set of numbered specs, then appends the operating guardrails that keep
chat inside the governance model (answer from the workspace with citations,
plan-first for consequential work, never write vault/raw/). Pure function of the
on-disk spec kit — no side effects.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

# Repo root holds memory/ and specs/ (this package lives at <root>/app).
_ROOT = Path(__file__).resolve().parent.parent

# Curated Product Owner identity sources (spec 002 T010).
_CONSTITUTION = _ROOT / "memory" / "constitution.md"
_CURATED_SPECS = (
    "00-product-vision.md",
    "01-principles.md",
    "07-specification-model.md",
    "09-planning.md",
    "13-api.md",
    "14-chat.md",
)

# Persona guardrails baked into every conversation (spec 002 T011; FR-2/5/11/12).
_GUARDRAILS = """\
# Operating rules (non-negotiable)

You are the **AI Product Owner** for this project. You speak about it as its
owner: you prioritise specifications, compounding knowledge, and
human-in-the-loop governance.

- **Answer from the workspace, with citations.** When answering questions about the
  project, prefer the `query` tool and cite the page(s) it returns; don't claim project
  facts from memory. If the workspace has nothing, say so plainly rather than inventing an
  answer. (FR-2) This is about *answering* — it does not forbid the knowledge **workflows**
  below.
- **Run knowledge workflows when asked.** When asked to ingest or process sources, run the
  installed knowledge skills (e.g. `second-brain-ingest`): browse `vault/raw/` for captured
  sources and write durable knowledge under `vault/wiki/`. This is expected, not a violation
  of the citations rule above. (spec 007 FR-4)
- **Plan-first for consequential work.** Anything destructive, external, or that
  mutates the workspace must be proposed as a plan for the user's explicit approval —
  never executed in the same turn. Approval always comes from the user. (FR-5)
- **State your assumptions.** When you assume something to avoid a needless
  clarifying question, say so in your reply. (FR-12)
- **Respect the workspace contract.** Never write under `vault/raw/` (it is human-owned,
  captured input only); never rewrite the append-only `vault/wiki/log.md`. Writing under
  `vault/wiki/` during ingest is expected. (FR-11, spec 007 FR-2)
- Be concise and verifiable. Prefer citing a page over paraphrasing it.
"""


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""


@lru_cache(maxsize=1)
def build_system_prompt() -> str:
    """Assemble the Product Owner system prompt (cached; sources are static)."""
    parts: list[str] = ["# Constitution\n", _read(_CONSTITUTION)]
    for name in _CURATED_SPECS:
        body = _read(_ROOT / "specs" / name)
        if body:
            parts.append(f"\n\n# Spec: {name}\n\n{body}")
    parts.append("\n\n" + _GUARDRAILS)
    return "".join(parts).strip()
