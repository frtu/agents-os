"""Ingest activity wrapper — the "uber package" (spec 007 FR-6).

`activity_ingest` fits the activity interface (``ActivityInput`` → ``ActivityOutput``,
spec 007 FR-5) and bridges to the ``second-brain-ingest`` skill run **headless**, which it
**never modifies** (FR-4/D6). It reconciles the skill's assumed layout (``raw/``, ``wiki/``,
``wiki/index.md``) with the workspace's real layout by **injecting context** — the overlaid
foundation-doc contract (core + extension, extension-wins per spec 22 R5, FR-11) plus the
path mapping — around the skill rather than editing it.

Two-phase headless bridge (FR-6 / AC-4):
  * **phase 1** — inject context + parameters, run the skill headless, collect its
    **unstructured** output;
  * **phase 2** — run headless **again** to coerce that output into the pydantic
    ``ActivityOutput`` (a progress list + an error list).

When the ``claude-agent-sdk`` runtime is unavailable (no CLI / credentials), the phases
raise ``AgentUnavailable`` so the capability layer can apply its deterministic offline
fallback (spec 007 FR-7). Building the overlay context is pure and offline-testable.
"""

from __future__ import annotations

import json
from pathlib import Path

from . import config, models
from .agent import AgentUnavailable

# MCP/native tools the ingest activity may use. Unlike the removed narrow `ingest` tool
# (FR-12), the skill runs with real file tools scoped to the workspace so it can browse
# vault/raw/ and write vault/wiki/ (the raw-write guard still blocks vault/raw/ writes, FR-13).
_ACTIVITY_TOOLS = ["Skill", "Bash", "Read", "Write", "Edit", "Glob", "Grep"]


def _overlay_for(workspace: Path, name: str) -> str:
    """Render one foundation doc as `core` overlaid by its `extension` (spec 22 R5, FR-11)."""
    docs = workspace / "vault" / "docs"
    core = docs / f"{name}.md"
    ext = docs / f"{name}-extension.md"
    core_text = core.read_text(encoding="utf-8", errors="ignore") if core.is_file() else "(missing)"
    ext_text = ext.read_text(encoding="utf-8", errors="ignore") if ext.is_file() else "(no extension)"
    return (
        f"### {name} (effective contract = core + extension; extension wins)\n\n"
        f"#### core: {name}.md\n{core_text}\n\n"
        f"#### extension (authoritative overrides): {name}-extension.md\n{ext_text}\n"
    )


def build_overlay_context(workspace: Path) -> str:
    """Assemble the injected runtime context for the activity (spec 007 FR-11).

    Concatenates the overlaid foundation-doc contracts and states the concrete path mapping
    so the unmodified skill resolves this workspace's real paths.
    """
    parts = [
        "# Injected workspace contract (do not edit the core; extension wins — spec 22 R5)\n",
        "## Path mapping (skill layout → this workspace)\n"
        "- `raw/` → `vault/raw/`\n"
        "- `wiki/` → `vault/wiki/`\n"
        "- index file `wiki/index.md` → `vault/wiki/portal.md`\n"
        "- foundation docs live under `vault/docs/`\n"
        "- unprocessed-work backlog: `vault/wiki/tbd.md` (grouped by topic & theme)\n",
    ]
    for name in ("wiki-schema", "wiki-architecture"):
        parts.append(_overlay_for(workspace, name))
    return "\n".join(parts)


def build_input(workspace_name: str, workspace_path: Path, raw_selection: list[str] | None = None) -> models.ActivityInput:
    """Construct the activity Input Object, injecting the overlay context (FR-5/FR-11)."""
    return models.ActivityInput(
        workspace=workspace_name,
        workspace_path=str(workspace_path),
        raw_selection=raw_selection or [],
        context=build_overlay_context(workspace_path),
    )


_PHASE1_SYSTEM = (
    "You are running the `second-brain-ingest` activity headless. Use the injected workspace "
    "contract to resolve real paths. Read `vault/wiki/tbd.md` for unprocessed work, process "
    "captured sources under `vault/raw/`, and write durable knowledge under `vault/wiki/` "
    "(source summaries, portal, log). NEVER write under `vault/raw/`. Update `vault/wiki/tbd.md` "
    "as you complete items. Report what you did in plain text."
)

_PHASE2_SYSTEM = (
    "Convert the ingest run report below into JSON with exactly two keys: `progress` (a list of "
    "strings describing what was processed/created/updated) and `errors` (a list of strings "
    "describing failures). Output ONLY the JSON object, nothing else."
)


async def run(inp: models.ActivityInput) -> models.ActivityOutput:
    """Run the ingest activity via the two-phase headless bridge (spec 007 FR-6/AC-4).

    Raises ``AgentUnavailable`` when the runtime is absent so ``capabilities.ingest`` can
    fall back deterministically (FR-7).
    """
    workspace_path = Path(inp.workspace_path)
    prompt = (
        f"{inp.context}\n\n"
        f"Selected raw sources: {inp.raw_selection or 'ALL captured sources'}\n\n"
        "Run the second-brain-ingest activity now over the unprocessed work."
    )
    # phase 1 — run the skill, collect unstructured output
    unstructured = await _headless(_PHASE1_SYSTEM, prompt, workspace_path)
    # phase 2 — coerce the unstructured output into the Output Object
    structured = await _headless(_PHASE2_SYSTEM, unstructured, workspace_path, tools=[])
    return _parse_output(structured)


def _parse_output(text: str) -> models.ActivityOutput:
    """Best-effort parse of the phase-2 JSON into an ActivityOutput (progress + errors)."""
    start, end = text.find("{"), text.rfind("}")
    if start != -1 and end > start:
        try:
            data = json.loads(text[start : end + 1])
            return models.ActivityOutput(
                progress=[str(x) for x in data.get("progress", [])],
                errors=[str(x) for x in data.get("errors", [])],
            )
        except (json.JSONDecodeError, TypeError, AttributeError):
            pass
    # Non-JSON output is still a valid (degraded) result: treat the text as one progress note.
    return models.ActivityOutput(progress=[text.strip()[:400]] if text.strip() else [], errors=[])


async def _headless(  # pragma: no cover — requires the live SDK runtime/credentials
    system_prompt: str, message: str, workspace_path: Path, tools: list[str] | None = None
) -> str:
    """Run one headless turn and return the accumulated text (spec 007 FR-6).

    Thin wrapper over ``claude-agent-sdk``; raises ``AgentUnavailable`` when the runtime or
    credentials are missing so the caller can fall back (FR-7). Not exercised by the offline
    test suite (the deterministic fallback path is).
    """
    try:
        from claude_agent_sdk import (
            ClaudeAgentOptions,
            CLINotFoundError,
            HookMatcher,
            ResultMessage,
            TextBlock,
            query,
        )
    except ImportError as e:
        raise AgentUnavailable(str(e)) from e

    from .agent import _raw_guard_hook  # reuse the P2 raw-guard hook (FR-13)

    allowed = _ACTIVITY_TOOLS if tools is None else tools
    opts = ClaudeAgentOptions(
        system_prompt=system_prompt,
        model="sonnet",
        allowed_tools=allowed,
        permission_mode="bypassPermissions",
        setting_sources=["project"],
        skills="all",
        cwd=str(workspace_path),
        add_dirs=[str(workspace_path), str(config.skills_library_root())],
        hooks={"PreToolUse": [HookMatcher(hooks=[_raw_guard_hook(workspace_path)])]},
    )
    out = ""
    try:
        async for m in query(prompt=message, options=opts):
            for block in getattr(m, "content", []) or []:
                if isinstance(block, TextBlock):
                    out += block.text
            if isinstance(m, ResultMessage):
                out = getattr(m, "result", None) or out
    except CLINotFoundError as e:
        raise AgentUnavailable("claude CLI not found") from e
    except Exception as e:  # noqa: BLE001 — treat runtime failures as unavailability
        raise AgentUnavailable(str(e)) from e
    return out
