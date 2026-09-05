"""Agent runtime adapter (spec 002 T021/T022; D3 · spec 005 FR-8/9/10 · spec 006).

The assistant reaches the model through ``claude-agent-sdk``. Its in-process MCP server
**mirrors the whole capability layer** (spec 006 FR-3): every capability function is an
agent tool, minus a governed exclusion set. The chat surface (``ask``/``ask_stream``) is
**structurally excluded** — never registered — so the agent cannot re-enter chat and
recurse (spec 006 D4). A **config-driven blacklist** (``config.mcp_tool_blacklist()``,
default ``{chat, upload, create_workspace}``) withholds further tools; ``upload`` stays
human-only so the agent cannot write ``vault/raw/`` (P2), and ``create_workspace`` keeps
the agent scoped to its active workspace (spec 006 D2/D3). Every tool is **workspace-bound**
— the workspace argument is injected from the run context, not from tool args (spec 006
FR-6). ``query`` remains the cited way to browse knowledge (FR-5).

``get_settings``/``update_settings`` are **structurally excluded** like ``chat``: trust mode
(``auto_approve``) is standing consent the operator alone grants, so the agent gets no tool to
set it, read it, or bypass the approval gate with it (spec 009 FR-11/FR-12).

**Skill execution (feature 005) deliberately expands the tool set.** To let the agent
discover and run installed skills, it is granted real ``Skill``/``Bash``/``Read``/
``Write``/``Edit``/``Glob``/``Grep`` tools, scoped to the active workspace via ``cwd``
and ``add_dirs`` and run under ``bypassPermissions``. This reverses the citations-only
browse boundary of feature 002 D3 *for skill execution* (spec 005 D3). Skill discovery
requires ``setting_sources=["project"]`` (an empty list disables skills entirely).

Because ``can_use_tool`` is not consulted under ``bypassPermissions``, the **PreToolUse hook** is
the only mechanism that can actually deny a tool call, which makes it the enforcement point for
everything the agent does (spec 011 FR-4, D2). ``_pretooluse_hook`` applies two gates in order:
``vault/raw/`` immutability (P2, spec 005 FR-10), which is absolute and consults nothing; then the
announce/permit contract of spec 011 FR-3, which puts every native tool call under the same risk
gate as a capability call. The per-workspace git repo remains the backstop for the residual
Bash-write risk (spec 005 D3).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import AsyncIterator, Awaitable, Callable

from . import conversation, execution_gate, models, vault
from .execution_gate import Operation

_SERVER = "leader"

# Native tools granted for skill execution (spec 005 FR-9), alongside the MCP tools.
_NATIVE_TOOLS = ["Skill", "Bash", "Read", "Write", "Edit", "Glob", "Grep"]


class AgentUnavailable(RuntimeError):
    """Raised when the agent runtime cannot be reached (missing CLI/credentials)."""


@dataclass
class ToolSpec:
    """One agent MCP tool: its name/description/schema and an async handler (spec 006).

    The handler closes over the run's active workspace selector, so the tool is
    workspace-bound (FR-6) and unit-testable without the SDK.
    """

    name: str
    description: str
    schema: dict
    handler: Callable[[dict], Awaitable[dict]]


def _ok(text: str) -> dict:
    """SDK tool-content shape for a text result."""
    return {"content": [{"type": "text", "text": text}]}


def _capability_tool_specs(
    workspace_selector: str | None,
    citations: list[models.Citation],
    conversation_id: str | None = None,
    interactions: list[models.Interaction] | None = None,
    trust: bool = False,
    naming: list[tuple[str, list[str]]] | None = None,
) -> list[ToolSpec]:
    """Build an agent tool for every exposable capability (spec 006 FR-3/FR-4).

    Pure and SDK-free: handlers call ``capabilities`` directly. Every handler injects
    ``workspace_selector`` and ignores any ``workspace`` in tool args (the sandbox,
    FR-6). The chat surface is deliberately absent (structural exclusion, D4). The mutating
    tool ``import_skill`` executes directly (spec 005 D1); the narrow ``ingest`` tool was
    removed (spec 007 FR-12) — ingest now runs as the bottom-up workflow. ``request_interaction``
    lets the agent raise a clarification/notification card on its own (spec 008 FR-18), bound to
    the run's ``conversation_id``; cards it raises are appended to ``interactions`` for the caller.

    ``request_approval`` lets it **request** consent through the governed channel (spec 010 FR-1).
    ``trust`` is the effective trust mode, closed over from the capability layer and absent from
    every tool schema — the agent can neither read nor set it, and so can never grant its own
    request (spec 010 FR-2, spec 009 FR-11).

    ``name_conversation`` is turn-local (spec 012 FR-4): it reaches no workspace, only appending the
    agent's proposed title to ``naming`` for the capability layer to apply at materialization.
    """
    from . import capabilities  # lazy import to avoid an agent<->capabilities cycle

    async def query_h(args: dict) -> dict:
        ans = capabilities.query(
            models.QueryRequest(workspace=workspace_selector, question=args["question"])
        )
        citations.extend(ans.citations)  # surfaced to the caller for the reply (FR-5)
        lines = [ans.answer, ""]
        for c in ans.citations:
            lines.append(f"- {c.page}: {c.excerpt}")
        return _ok("\n".join(lines))

    async def spec_read_h(args: dict) -> dict:
        try:
            text = capabilities.spec_read(args["path"], workspace_selector)
        except Exception as e:  # noqa: BLE001 — surface as tool text, not a crash
            return _ok(f"error: {e}")
        return _ok(text[:4000])

    async def plan_h(args: dict) -> dict:
        p = capabilities.plan(
            models.PlanRequest(workspace=workspace_selector, request=args["request"])
        )
        steps = "\n".join(f"{s.order}. {s.action} — {s.rationale}" for s in p.steps)
        return _ok(f"risk={p.risk} requires_approval={p.requires_approval}\n{steps}")

    async def list_workspaces_h(args: dict) -> dict:
        return _ok(capabilities.list_workspaces().model_dump_json(indent=2))

    async def get_workspace_info_h(args: dict) -> dict:
        return _ok(capabilities.get_workspace_info(workspace_selector).model_dump_json(indent=2))

    async def lint_h(args: dict) -> dict:
        return _ok(capabilities.lint(workspace_selector).model_dump_json(indent=2))

    async def wiki_tree_h(args: dict) -> dict:
        return _ok(capabilities.wiki_tree(workspace_selector).model_dump_json(indent=2))

    async def list_conversations_h(args: dict) -> dict:
        return _ok(capabilities.list_conversations(workspace_selector).model_dump_json(indent=2))

    async def get_conversation_h(args: dict) -> dict:
        try:
            detail = capabilities.get_conversation(workspace_selector, args["conversation_id"])
        except Exception as e:  # noqa: BLE001
            return _ok(f"error: {e}")
        return _ok(detail.model_dump_json(indent=2))

    async def conversation_status_h(args: dict) -> dict:
        status = capabilities.conversation_status(workspace_selector, args["conversation_id"])
        return _ok(status.model_dump_json(indent=2))

    async def list_available_skills_h(args: dict) -> dict:
        return _ok(capabilities.list_available_skills(workspace_selector).model_dump_json(indent=2))

    async def list_installed_skills_h(args: dict) -> dict:
        return _ok(capabilities.list_installed_skills(workspace_selector).model_dump_json(indent=2))

    async def import_skill_h(args: dict) -> dict:
        try:
            report = capabilities.import_skill(workspace_selector, args["name"])
        except Exception as e:  # noqa: BLE001
            return _ok(f"error: {e}")
        return _ok(report.model_dump_json(indent=2))

    def best_name() -> str:
        """The best conversation name known right now (spec 012 FR-5).

        ``naming`` is seeded with the fallback and appended to by ``name_conversation``, so the last
        entry is always the best title available — which a card that materializes the record
        mid-turn needs, since it may write the file before the turn's first ``append_turn``.
        """
        return naming[-1][0] if naming else ""

    async def request_interaction_h(args: dict) -> dict:
        # spec 008 FR-18: the agent raises its own clarification/notification card. Approval is
        # deliberately not offered here — it stays with the plan-first path (FR-14/FR-17).
        import json

        kind = (args.get("kind") or "").strip()
        if kind not in ("clarification", "notification"):
            return _ok("error: kind must be 'clarification' or 'notification' (approval is plan-first only)")
        raw = args.get("options") or ""
        options: list = []
        if raw.strip():
            try:
                parsed = json.loads(raw)
            except (ValueError, TypeError):
                return _ok('error: options must be a JSON array, e.g. ["Approach A","Approach B"]')
            options = parsed if isinstance(parsed, list) else [parsed]
        try:
            itx = capabilities.create_interaction(
                workspace_selector, conversation_id, kind, args.get("prompt", ""), options,
                name_hint=best_name(),
            )
        except Exception as e:  # noqa: BLE001 — surface as tool text so the model can adjust (FR-15/FR-6)
            return _ok(f"error: {e}")
        if interactions is not None:
            interactions.append(itx)
        return _ok(f"raised {kind} interaction {itx.interaction_id} ({len(itx.options)} option(s))")

    async def request_approval_h(args: dict) -> dict:
        # spec 010 FR-1/FR-2: the agent asks; the capability layer decides, from the operator's
        # trust mode closed over here. No argument can influence the outcome.
        prompt = (args.get("prompt") or "").strip()
        if not prompt:
            return _ok("error: prompt is required — state exactly what you intend to do")
        try:
            itx, granted = capabilities.request_approval(
                workspace_selector, conversation_id, prompt, args.get("detail", ""), trust=trust,
                name_hint=best_name(),
            )
        except Exception as e:  # noqa: BLE001 — surface as tool text so the model can adjust
            return _ok(f"error: {e}")
        if interactions is not None:
            interactions.append(itx)
        if granted:
            return _ok(
                f"APPROVED on the operator's behalf (trust mode is on) — interaction "
                f"{itx.interaction_id}. You are authorised to proceed: carry out the work you just "
                "described now, in this same turn, and report what you did. Do not ask again."
            )
        return _ok(
            f"NOT APPROVED YET — blocking approval card {itx.interaction_id} is now awaiting the "
            "user. STOP here and take no action. Do not perform the work, do not ask again in prose, "
            "and do not use any mutating tool. End your turn by stating that you are waiting for "
            "their decision; the turn resumes automatically once they answer."
        )

    async def name_conversation_h(args: dict) -> dict:
        # spec 012 FR-4: the proposal is collected, not written. The store applies the last one at
        # materialization, so this tool touches no workspace and needs no capability function.
        title = (args.get("title") or "").strip()
        if not title:
            return _ok("error: title is required — a short descriptive name for this conversation")
        raw = args.get("tags") or ""
        tags = [t for t in (part.strip().lower() for part in raw.split(",")) if t][:4]
        if naming is not None:
            naming.append((title, tags))
        return _ok(f"named: {conversation.slugify(title)}")

    return [
        ToolSpec("query", "Search the workspace and return an answer with citations. The primary way to browse project knowledge.", {"question": str}, query_h),
        ToolSpec("spec_read", "Read the raw Markdown of a known workspace page by its relative path.", {"path": str}, spec_read_h),
        ToolSpec("plan", "Describe what a work request would actually do — the capability it runs, its target, effect tier and undo path. Only an executable, approval-tier effect is flagged for approval.", {"request": str}, plan_h),
        ToolSpec("list_workspaces", "List known workspaces (names, root, default).", {}, list_workspaces_h),
        ToolSpec("get_workspace_info", "Inspect the active workspace: name, path, whether scaffolded, and page count.", {}, get_workspace_info_h),
        ToolSpec("lint", "Run hygiene checks (orphan/short pages) on the active workspace.", {}, lint_h),
        ToolSpec("wiki_tree", "Browse the active workspace's vault/wiki/ tree (navigation only).", {}, wiki_tree_h),
        ToolSpec("list_conversations", "List prior conversations in the active workspace.", {}, list_conversations_h),
        ToolSpec("get_conversation", "Read one conversation's full turns by its id.", {"conversation_id": str}, get_conversation_h),
        ToolSpec("conversation_status", "Report whether a conversation has a turn in progress on the server (running) and whether it exists.", {"conversation_id": str}, conversation_status_h),
        ToolSpec("list_available_skills", "List skills available to install from the shared library, each with a description and an installed flag.", {}, list_available_skills_h),
        ToolSpec("list_installed_skills", "List skills currently installed in the active workspace.", {}, list_installed_skills_h),
        # spec 007 FR-12: the narrow `ingest` MCP tool is removed. Ingest runs as the bottom-up
        # workflow (capabilities.ingest → activity_ingest), not a constrained {title,content} tool.
        ToolSpec("import_skill", "Reference-link a shared-library skill into the active workspace and commit.", {"name": str}, import_skill_h),
        ToolSpec(
            "request_interaction",
            "Ask the user via a distinct interaction card instead of prose. Use kind='clarification' when "
            "the request is genuinely ambiguous or needs a choice among 2-4 distinct approaches (pass "
            "'options' as a JSON array of short labels; this PAUSES the turn until the user picks). Use "
            "kind='notification' for brief non-blocking status (options='[]'). Do NOT use for approvals of "
            "consequential/destructive work (those are handled automatically) and do NOT raise a card when "
            "the request is already clear.",
            {"kind": str, "prompt": str, "options": str},
            request_interaction_h,
        ),
        ToolSpec(
            "request_approval",
            "Request the operator's consent before doing work you judge consequential (destructive, "
            "irreversible, external, or a large batch of mutations). ALWAYS use this instead of asking "
            "for approval in prose — a prose approval cannot be recorded, re-presented, or answered. "
            "'prompt' states exactly what you intend to do; 'detail' adds the effect and whether it is "
            "reversible. The result tells you whether you are authorised: if approved, do the work now "
            "in this same turn; if not, stop and take no action. You cannot approve your own request.",
            {"prompt": str, "detail": str},
            request_approval_h,
        ),
        ToolSpec(
            "name_conversation",
            "Give this conversation a short descriptive title (3-8 words) plus 1-4 comma-separated "
            "lowercase tags. Call this ONCE, early in your first reply of a new conversation. The "
            "title becomes the conversation's durable filename and the label the user sees in their "
            "session list, and it CANNOT be changed later — so name the subject of the request, not "
            "your answer. Skip it when continuing an existing conversation.",
            {"title": str, "tags": str},
            name_conversation_h,
        ),
    ]


def _selected_specs(
    workspace_selector: str | None,
    citations: list[models.Citation],
    blacklist: set[str],
    conversation_id: str | None = None,
    interactions: list[models.Interaction] | None = None,
    trust: bool = False,
    naming: list[tuple[str, list[str]]] | None = None,
) -> list[ToolSpec]:
    """Capability tools minus the blacklist (spec 006 FR-2). Chat is already absent (D4)."""
    specs = _capability_tool_specs(
        workspace_selector, citations, conversation_id, interactions, trust, naming
    )
    return [s for s in specs if s.name not in blacklist]


def _allowed_tool_names(specs: list[ToolSpec]) -> list[str]:
    """Fully-qualified MCP tool names for ``allowed_tools`` (spec 006 FR-8)."""
    return [f"mcp__{_SERVER}__{s.name}" for s in specs]


def _raw_guard_decision(workspace_path: Path, tool_name: str, tool_input: dict) -> str | None:
    """Pure raw-guard: return a deny reason if a tool call would write vault/raw/, else None.

    Enforces P2 for the autonomous agent (spec 005 FR-10). Path-based for the file tools;
    heuristic for Bash (a shell redirect can still evade this — git is the backstop, D3).
    """
    if tool_name in ("Write", "Edit", "NotebookEdit"):
        raw = tool_input.get("file_path") or tool_input.get("notebook_path")
        if not raw:
            return None
        target = Path(raw)
        if not target.is_absolute():
            target = workspace_path / target
        try:
            vault.guard_write_path(workspace_path, target)
        except vault.WorkspaceError as e:
            return str(e)
        return None
    if tool_name == "Bash":
        command = tool_input.get("command", "")
        if "vault/raw" in command and any(
            tok in command
            for tok in (">", "tee ", "cp ", "mv ", "rm ", "truncate", "sed -i", "dd ", "mkdir", "touch ")
        ):
            return "vault/raw/ is immutable; refusing Bash write into vault/raw/ (spec 005 FR-10)"
    return None


# --- native tool → Operation mapping (spec 011 FR-5, D2) ------------------------------
#
# The effect metadata for the agent's OWN tools, declared as data exactly as `capabilities.EFFECTS`
# is for capability calls. This is what puts native tool calls under the same gate as capabilities
# (FR-4/FR-6, AC-3) — previously every Write and Bash outside vault/raw/ ran unobserved.
#
# Tiers stay deliberately coarse; the fine-grained judgment is layer 2's scoring modifiers (D3).
# Bash is the interesting case: this entry is the *unrecognised* case, declared `reversible` because
# a command's usual effect is on workspace files, and the DESTRUCTIVE_SHELL modifier is what lifts
# `rm -rf` to a gating score. A command recognised as read-only is declared `auto` instead
# (spec 011 FR-39) — see `_operation_for_tool`.
# The undo path for a mutation that stays inside the workspace repo. Shared so a shell command
# confined to the workspace is priced exactly like the equivalent `Write` (FR-42), and so the wording
# layer 2 pattern-matches cannot drift between the two.
_GIT_COVERED = "`git revert` the turn's commit in the workspace repo"

_TOOL_EFFECTS: dict[str, tuple[str, str]] = {
    "Read": ("auto", "read-only — nothing to undo"),
    "Glob": ("auto", "read-only — nothing to undo"),
    "Grep": ("auto", "read-only — nothing to undo"),
    "Skill": ("auto", "loads instructions; any work it performs is announced as its own operations"),
    "Write": ("reversible", _GIT_COVERED),
    "Edit": ("reversible", _GIT_COVERED),
    "NotebookEdit": ("reversible", _GIT_COVERED),
    "Bash": ("reversible", "`git revert` covers workspace files; effects outside the repo are not undone"),
}

# Shell tokens whose effect leaves this machine, so it cannot be reverted at all (FR-5 `external`).
_EXTERNAL_SHELL_TOKENS = ("curl ", "wget ", "git push", "gh ", "ssh ", "scp ", "npm publish", "pip upload")

_FILE_PATH_KEYS = ("file_path", "notebook_path", "path")


def _tool_target(tool_name: str, tool_input: dict) -> str:
    """Best available resolved target for a tool call (spec 011 FR-5)."""
    for key in _FILE_PATH_KEYS:
        if tool_input.get(key):
            return str(tool_input[key])
    if tool_name == "Bash":
        return str(tool_input.get("command", ""))
    return str(tool_input.get("pattern") or tool_input.get("command") or "")


# The argument that names what a capability tool acts on, per capability. Used to give the
# announcement a real target instead of an opaque tool name (spec 011 FR-5).
_CAPABILITY_TARGET_ARGS = ("name", "title", "path", "question", "request", "prompt")

_MCP_PREFIX = f"mcp__{_SERVER}__"


def _operation_for_capability_tool(capability: str, tool_input: dict) -> Operation:
    """Describe an MCP capability tool call as an Operation (spec 011 FR-5/FR-6).

    Reads the tier straight from ``capabilities.EFFECTS`` — the same declared effect metadata the
    REST path uses — so a capability is scored identically however it was reached (P9 parity).
    """
    from . import capabilities

    effect = capabilities.EFFECTS.get(capability)
    tier = effect.tier if effect else "reversible"
    reversibility = effect.reversibility if effect else "unknown undo path"
    target = next((str(tool_input[k]) for k in _CAPABILITY_TARGET_ARGS if tool_input.get(k)), "")
    return Operation(
        kind="capability",
        name=capability,
        target=target,
        tier=tier,
        reversibility=reversibility,
        # Same declared-risk resolution the REST and chat doors use, so a skill the *agent* installs
        # is scored from its declared level too, not the reversibility modifiers (spec 011 FR-37, P9).
        declared_risk=capabilities.declared_risk_for(capability, target),
    )


def _confined_to_workspace(workspace_path: Path, command: str) -> bool:
    """Does every path this command names sit inside the workspace repo (spec 011 FR-42)?

    Requires at least one resolvable path and **all** of them inside, so a command naming nothing
    resolvable (`git commit -m "…"`) keeps the pessimistic declaration rather than earning a
    downgrade by saying nothing. An unresolvable token — a variable, a `~` — counts as outside.
    """
    tokens = execution_gate.path_tokens(command)
    if not tokens:
        return False
    try:
        root = workspace_path.resolve()
    except (OSError, ValueError):
        return False
    for token in tokens:
        if token.startswith("~") or token.startswith("$"):
            return False
        candidate = Path(token)
        if not candidate.is_absolute():
            candidate = workspace_path / candidate
        try:
            if not candidate.resolve().is_relative_to(root):
                return False
        except (OSError, ValueError):
            return False
    return True


def _git_recoverable(command: str) -> bool:
    """Does every path this command names sit inside some enclosing git repo (spec 011 FR-51)?

    Broader than `_confined_to_workspace`: a write into any working tree with a `.git` ancestor —
    the project repo included — is undone by that repo's `git revert`, not only the per-workspace one.
    Deterministic, no shelling out: resolve each token and walk its parents for a `.git` entry.
    Requires at least one resolvable path and **all** of them recoverable, matching FR-42's unanimous
    rule; an unresolvable token (`~`, `$VAR`) counts as outside, the safer reading.
    """
    tokens = execution_gate.path_tokens(command)
    if not tokens:
        return False
    for token in tokens:
        if token.startswith("~") or token.startswith("$"):
            return False
        try:
            resolved = Path(token).resolve()
        except (OSError, ValueError):
            return False
        # A create names a path that does not exist yet; the enclosing dir is what must be in a repo.
        start = resolved if resolved.exists() else resolved.parent
        if not any((parent / ".git").exists() for parent in (start, *start.parents)):
            return False
    return True


def _names_sensitive_target(command: str) -> bool:
    """Does the command name a sensitive control file (spec 011 FR-51/FR-8)?

    The FR-51 git-recoverable downgrade must not rescue a write to the ledger, the git database, the
    operator's trust settings or the constitution: `SENSITIVE_TARGET` weighs only 1 and does not gate
    on its own, so it relies on the pessimistic reversibility staying in place. Uses the execution
    layer's shared marker list so layer 1 and layer 2 never drift.
    """
    target = execution_gate.strip_heredocs(command).replace("\\", "/")
    return any(marker in target for marker in execution_gate.SENSITIVE_TARGET_MARKERS)


def _operation_for_tool(workspace_path: Path, tool_name: str, tool_input: dict) -> Operation:
    """Describe a tool call as an announceable Operation (spec 011 FR-5).

    Covers both surfaces the agent has: its **native** tools and its **MCP capability** tools. Both
    arrive at the same PreToolUse hook, so one enforcement point serves both and there is no second
    mechanism to keep in sync (FR-4, D2).

    A write whose target resolves **outside** the workspace is escalated to the `approval` tier: the
    workspace git repo is what makes a mutation reversible (P8), and it does not reach beyond its own
    root, so no revert here can undo that write.

    A shell command recognised as **read-only** is declared `auto` rather than `reversible` (FR-39),
    so inspecting the workspace is not scored as changing it. Recognition is positive and the
    external-token check is applied first, so anything unrecognised keeps the pessimistic tier.

    A shell command that mutates but stays **inside** the workspace is declared with the git-covered
    undo path, the same one `Write` gets (FR-42), so `mkdir -p vault/wiki/…` is not priced as if it
    might have escaped the repo.
    """
    if tool_name.startswith(_MCP_PREFIX):
        return _operation_for_capability_tool(tool_name[len(_MCP_PREFIX):], tool_input)

    tier, reversibility = _TOOL_EFFECTS.get(tool_name, ("reversible", "unknown undo path"))
    target = _tool_target(tool_name, tool_input)
    # FR-45: classify the command, never the heredoc payload it writes.
    classifiable = execution_gate.strip_heredocs(target) if tool_name == "Bash" else target
    external = tool_name == "Bash" and (
        any(tok in classifiable for tok in _EXTERNAL_SHELL_TOKENS)
        or execution_gate.has_external_reach(classifiable)
    )

    if tool_name == "Bash" and not external and execution_gate.is_safe_shell(target):
        # Read-only (FR-39) or safe-create (FR-50, `mkdir`) — announced `auto`, so it never reaches
        # the gate. `is_safe_shell` is the read-only set plus `mkdir`; a create has no content to
        # revert, so the read-only reversibility wording is accurate enough.
        tier = "auto"
        reversibility = execution_gate.READ_ONLY_SHELL_REVERSIBILITY
    elif tool_name == "Bash" and not external and (
        _confined_to_workspace(workspace_path, target)
        or (_git_recoverable(target) and not _names_sensitive_target(target))
    ):
        # A real external call has no git undo, so `external` still short-circuits confinement. What
        # FR-45 fixes is *what sets* `external`: a heredoc payload that merely mentions `curl` no
        # longer does, so a page whose own prose names a tool keeps its git-covered undo path.
        # FR-51: a write into any enclosing git repo (e.g. `specs/` in the project repo, not just the
        # workspace) is git-covered too, so spec authoring is `reversible`, not irreversible — but a
        # SENSITIVE_TARGET (constitution, log, settings) keeps the pessimistic declaration so it still
        # gates, since SENSITIVE_TARGET alone does not reach the threshold.
        reversibility = _GIT_COVERED

    if tier == "reversible" and tool_name in ("Write", "Edit", "NotebookEdit") and target:
        resolved = Path(target)
        if not resolved.is_absolute():
            resolved = workspace_path / resolved
        try:
            inside = resolved.resolve().is_relative_to(workspace_path.resolve())
        except (OSError, ValueError):  # unresolvable path — treat as outside, the safer reading
            inside = False
        if not inside:
            tier = "approval"
            reversibility = "outside the workspace repo; no git revert here covers it"

    return Operation(
        kind="tool",
        name=tool_name,
        target=target,
        tier=tier,
        reversibility=reversibility,
        external=external,
    )


def _pretooluse_hook(workspace_path: Path):
    """The PreToolUse hook — the enforcement point for the agent's native tools (spec 011 FR-4, D2).

    Two gates, in this order:

    1. **The raw guard (P2).** Absolute and unconditional: no score, verdict or trust setting can
       satisfy it (spec 011 AC-20), so it is checked before anything else and never consults layer 2.
    2. **The announce/permit contract (FR-2/FR-3).** Every other tool call is announced to whatever
       gate is installed and denied if the permit says so.

    ``deny`` here is what makes a pause *enforced* rather than advised. The prose channel of spec 010
    asked the model to stop and could not make it; this can (FR-4). Being `async` is what lets the
    permit await a verdict at all (D2).
    """

    async def hook(input_data: dict, tool_use_id: str | None, context) -> dict:  # noqa: ANN001
        tool_name = input_data.get("tool_name", "")
        tool_input = input_data.get("tool_input", {}) or {}

        reason = _raw_guard_decision(workspace_path, tool_name, tool_input)
        if reason:
            return _deny(reason)

        operation = _operation_for_tool(workspace_path, tool_name, tool_input)
        permit = await execution_gate.announce(operation)
        if not permit.allow:
            return _deny(execution_gate.deny_message(operation, permit))
        return {}

    return hook


def _deny(reason: str) -> dict:
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }


def _build_server(specs: list[ToolSpec]):
    """Build an in-process MCP server from selected capability tool specs (spec 006)."""
    from claude_agent_sdk import create_sdk_mcp_server, tool

    tools = [tool(s.name, s.description, s.schema)(s.handler) for s in specs]
    return create_sdk_mcp_server(_SERVER, "1.0.0", tools=tools)


async def run_stream(
    system_prompt: str,
    message: str,
    workspace_selector: str | None,
    workspace_path: Path,
    resume_sid: str | None,
    citations: list[models.Citation],
    conversation_id: str | None = None,
    interactions: list[models.Interaction] | None = None,
    trust: bool = False,
    naming: list[tuple[str, list[str]]] | None = None,
) -> AsyncIterator[tuple[str, str | None]]:
    """Stream (accumulated_reply, sdk_session_id) as the agent produces text.

    Mirrors the archived streaming pattern (query → init → text deltas → result). Runs
    workspace-scoped with skill discovery + native tools (spec 005 FR-8/9) and the
    raw-guard PreToolUse hook (FR-10).
    """
    try:
        from claude_agent_sdk import (
            ClaudeAgentOptions,
            CLINotFoundError,
            HookMatcher,
            ResultMessage,
            StreamEvent,
            SystemMessage,
            query,
        )
    except ImportError as e:  # pragma: no cover
        raise AgentUnavailable(str(e)) from e

    from . import config

    # Mirror the capability layer minus the blacklist; derive the server and
    # allowed_tools from the SAME selected set so registration and permission agree
    # (spec 006 FR-3/FR-8). Chat is never in the set (structural exclusion, D4).
    specs = _selected_specs(
        workspace_selector, citations, config.mcp_tool_blacklist(), conversation_id, interactions,
        trust, naming,
    )
    server = _build_server(specs)
    opts = ClaudeAgentOptions(
        system_prompt=system_prompt,
        model=config.agent_model(),
        mcp_servers={_SERVER: server},
        allowed_tools=[*_NATIVE_TOOLS, *_allowed_tool_names(specs)],
        permission_mode="bypassPermissions",
        setting_sources=["project"],  # MUST include a scope or skills are disabled (spec 005 risk 1)
        skills="all",
        cwd=str(workspace_path),
        add_dirs=[str(workspace_path), str(config.skills_library_root())],
        hooks={"PreToolUse": [HookMatcher(hooks=[_pretooluse_hook(workspace_path)])]},
        include_partial_messages=True,
        resume=resume_sid,
    )

    reply, sid = "", resume_sid
    try:
        async for m in query(prompt=message, options=opts):
            if isinstance(m, SystemMessage) and getattr(m, "subtype", "") == "init":
                sid = m.data.get("session_id", sid)
            elif isinstance(m, StreamEvent):
                ev = m.event
                if ev.get("type") == "content_block_delta" and ev.get("delta", {}).get("type") == "text_delta":
                    reply += ev["delta"]["text"]
                    yield reply, sid
            elif isinstance(m, ResultMessage):
                sid = getattr(m, "session_id", None) or sid
    except CLINotFoundError as e:
        raise AgentUnavailable("claude CLI not found") from e
    except Exception as e:  # noqa: BLE001 — treat runtime failures as unavailability
        raise AgentUnavailable(str(e)) from e
    yield reply, sid
