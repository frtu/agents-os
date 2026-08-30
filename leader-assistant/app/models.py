"""Request/response models for the capability layer and REST surface.

These are the JSON contracts shown in Swagger. Kept surface-agnostic so
chat and REST share identical shapes (Constitution P9, spec 13-api).
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class WorkspaceList(BaseModel):
    root: str = Field(..., description="Resolved workspace root directory")
    workspaces: list[str] = Field(default_factory=list, description="Scaffolded workspace names")
    default: str = Field(..., description="Default workspace selector")


class CreateWorkspaceRequest(BaseModel):
    name: str = Field(..., description="Workspace name to create under the root", examples=["_default_"])


class WorkspaceInfo(BaseModel):
    name: str
    path: str
    scaffolded: bool
    pages: int = Field(0, description="Count of Markdown pages under wiki/")


class IngestRequest(BaseModel):
    workspace: str | None = Field(None, description="Workspace selector; omitted = default")
    title: str = Field(..., description="Human title of the source", examples=["Team sync notes"])
    content: str = Field(..., description="Raw Markdown/text content to ingest")
    provenance: str = Field(
        "notes",
        description="raw/ subfolder signalling source type",
        examples=["notes", "clippings", "docs", "transcripts"],
    )


class IngestReport(BaseModel):
    workspace: str
    source_page: str = Field(..., description="Path of the created wiki/sources summary")
    portal_updated: bool
    committed: bool = Field(..., description="Whether a git commit was recorded")
    message: str
    # spec 007 FR-7: the ingest workflow surfaces the activity Output Object (progress + errors).
    progress: list[str] = Field(default_factory=list, description="What was processed / created / updated")
    errors: list[str] = Field(default_factory=list, description="What failed and why")


# --- activity interface (feature 007-knowledge-activities) ------------------
# The activity-agnostic contract every conforming activity implements (spec 007 FR-5).
# The compute unit (e.g. the `second-brain-ingest` skill) runs behind this contract so it
# stays interchangeable; the Output Object is exactly a progress list and an error list (D3).


class ActivityInput(BaseModel):
    """Parameters handed to an activity run (spec 007 FR-5).

    Activity-agnostic: carries the target workspace path plus the injected runtime context
    (path mapping / overlaid foundation-doc contract) the activity needs, never activity
    internals. `raw_selection` narrows which captured sources to process (empty = all).
    """

    workspace: str = Field(..., description="Workspace selector/name for the run")
    workspace_path: str = Field(..., description="Absolute path of the target workspace")
    raw_selection: list[str] = Field(
        default_factory=list,
        description="Captured raw paths (relative to the workspace) to process; empty = all",
    )
    context: str = Field(
        "", description="Injected runtime context: overlaid foundation-doc contract + path mapping (FR-11)"
    )


class ActivityOutput(BaseModel):
    """The activity's result — exactly a progress list and an error list (spec 007 FR-5, D3)."""

    progress: list[str] = Field(default_factory=list, description="Steps completed / artifacts created or updated")
    errors: list[str] = Field(default_factory=list, description="Failures encountered, each with a reason")


class QueryRequest(BaseModel):
    workspace: str | None = Field(None, description="Workspace selector; omitted = default")
    question: str = Field(..., description="Natural-language question", examples=["What decisions were made?"])


class Citation(BaseModel):
    page: str
    excerpt: str


class Answer(BaseModel):
    workspace: str
    question: str
    answer: str
    citations: list[Citation] = Field(default_factory=list)


class PlanRequest(BaseModel):
    workspace: str | None = None
    request: str = Field(..., description="Work request to plan", examples=["Refactor onboarding docs"])


class PlanStep(BaseModel):
    order: int
    action: str
    rationale: str


class Plan(BaseModel):
    """What will actually happen, so a review is informative (spec 009 FR-5).

    The effect fields name the real capability an approval authorizes; they are empty/`auto`
    when the request maps to no executable action, in which case `requires_approval` is false
    and no approval is ever raised (spec 009 FR-4).
    """

    workspace: str
    request: str
    steps: list[PlanStep]
    risk: str = Field(..., description="Risk outcome: safe | risky | reject")
    requires_approval: bool = Field(
        ..., description="Consequential work returns a plan for approval, never silent execution (spec 13-api AC2)"
    )
    capability: str = Field("", description="Executable capability this plan runs; empty = none (spec 009 FR-5)")
    target: str = Field("", description="What the capability acts on (workspace/skill/page)")
    effect_tier: str = Field("auto", description="Declared effect tier: auto | reversible | approval (FR-1)")
    reversibility: str = Field("", description="How the effect can be undone")


class LintFinding(BaseModel):
    kind: str = Field(..., description="orphan | stale | contradiction | missing")
    page: str
    detail: str


class LintReport(BaseModel):
    workspace: str
    findings: list[LintFinding] = Field(default_factory=list)
    ok: bool


# --- chat (feature 002-assistant-chat) -------------------------------------


class ChatRequest(BaseModel):
    """A single chat turn (spec 002 plan Data Contracts)."""

    message: str = Field(..., description="User message for this turn", examples=["What does the risk engine decide?"])
    workspace: str | None = Field(None, description="Vault selector; omitted = default (P13)")
    conversation_id: str | None = Field(
        None, description="Resume a prior conversation; omitted = start a new one (FR-3)"
    )
    approve: bool = Field(
        False, description="Approve the conversation's pending plan and execute it (FR-5, D2)"
    )
    auto_approve: bool | None = Field(
        None,
        description=(
            "Per-turn trust-mode override (spec 009 FR-7/FR-9): true runs an approval-tier action "
            "without prompting, false forces a prompt, omitted uses the persisted setting"
        ),
    )


class ChatAnswer(BaseModel):
    """Full (non-streamed) reply for a chat turn (FR-1)."""

    workspace: str
    conversation_id: str = Field(..., description="Durable id; resend to continue the thread (FR-3, FR-13)")
    reply: str
    citations: list[Citation] = Field(default_factory=list, description="Workspace pages supporting the reply (FR-2)")
    pending_plan: Plan | None = Field(
        None, description="Populated when the request is consequential and awaits approval (FR-5)"
    )
    executed: bool = Field(False, description="True when this turn approved and executed a stored plan (FR-5)")
    interaction: "Interaction | None" = Field(
        None, description="A pending agent→user interaction card raised by this turn (spec 008 FR-1/FR-2)"
    )


class ChatDelta(BaseModel):
    """One streamed chunk; the final delta carries done=true (FR-4)."""

    workspace: str
    conversation_id: str
    reply: str = Field(..., description="Accumulated reply so far")
    done: bool = Field(False, description="True on the final event")
    citations: list[Citation] = Field(default_factory=list)
    pending_plan: Plan | None = None
    executed: bool = False
    interaction: "Interaction | None" = Field(
        None, description="A pending agent→user interaction card raised by this turn (spec 008 FR-1/FR-2)"
    )


class ChatStatus(BaseModel):
    """Whether a conversation has a turn being processed server-side right now (FR-14).

    `running` is server-local, transient state (not part of the durable `sessions/`
    record, P1); `exists` reflects whether a durable record is on disk for the id.
    """

    workspace: str
    conversation_id: str
    running: bool = Field(
        ..., description="True while a chat turn for this conversation is in-flight on the server"
    )
    exists: bool = Field(
        ..., description="True when a durable session record exists for this conversation id"
    )


# --- agent<->user interaction (feature 008-agent-user-interaction) -----------


class InteractionOption(BaseModel):
    """One selectable proposal on an interaction card (spec 008 FR-5/FR-6).

    For an approval this is the single thing being consented to (rendered Yes/No);
    for a clarification these are the 2–4 distinct approaches. The constant
    "chat about it" affordance is NOT an option — it is added by every surface (FR-7).
    """

    id: str = Field(..., description="Stable option id referenced by an Interaction Response")
    label: str = Field(..., description="Short, human-readable choice text")
    detail: str = Field("", description="Optional rationale / longer description")


class Interaction(BaseModel):
    """A structured mid-task request from the backend for the user to notice or decide (spec 008 FR-2).

    `kind` is one of notification | approval | clarification. Option bounds (FR-6):
    notification=0, approval=1, clarification=2–4. `status` moves pending → resolved |
    expired | superseded; `resolution` records the chosen option id, "declined", or "timeout".

    A resolved+"auto-approved" approval carries **no** options: trust mode already decided it on
    the operator's behalf, so it is context to display, not a question to answer (spec 010 FR-5).
    """

    interaction_id: str = Field(..., description="Unique id, scoped to the conversation (FR-2)")
    conversation_id: str
    kind: str = Field(..., description="'notification' | 'approval' | 'clarification'")
    prompt: str = Field(..., description="Human-readable message / question")
    options: list[InteractionOption] = Field(
        default_factory=list, description="Proposals (0=notification, 1=approval, 2–4=clarification)"
    )
    timeout_seconds: int = Field(30, description="Countdown before the safe-default resolution (FR-9)")
    created: str = Field(..., description="ISO-8601 timestamp the request was (re-)presented")
    status: str = Field("pending", description="pending | resolved | expired | superseded")
    resolution: str | None = Field(
        None,
        description=(
            "Chosen option id, 'declined', 'timeout', or 'auto-approved' when trust mode granted "
            "consent on the operator's behalf (spec 010 FR-5)"
        ),
    )


# --- maker-checker risk contracts (feature 011-maker-checker-approval) --------
#
# The wire form of the layer-2 report. An approval card carries the whole accumulated list, not a
# single opaque action, so the operator sees the blast radius before consenting (FR-11, AC-5).


class RiskOperation(BaseModel):
    """One scored operation on a workflow run (spec 011 FR-7)."""

    op_id: str
    kind: str = Field(..., description="'capability' | 'tool'")
    name: str = Field(..., description="Capability name or tool name")
    target: str = Field("", description="Resolved target: path, workspace, skill, or command")
    tier: str = Field("auto", description="Declared effect tier: auto | reversible | approval")
    reversibility: str = Field("", description="How the effect can be undone")
    external: bool = Field(False, description="True when the effect leaves this machine")
    score: int = Field(1, ge=1, le=5, description="Risk score 1–5 = tier base + modifiers (FR-8)")
    modifiers: list[str] = Field(default_factory=list, description="Data-declared modifiers that fired (FR-8)")
    justification: str = Field("", description="One line: concrete effect + undo path (FR-10)")
    status: str = Field("pending", description="pending | executed | declined | not-reached")


class RiskAssessment(BaseModel):
    """Why a turn paused, and everything the operator needs to judge it (spec 011 FR-11/FR-14).

    `accumulated` is the gating operation **plus** every operation already executed in the run —
    the point being that approving is never a decision about one action in isolation.
    """

    run_id: str
    objective: str = Field("", description="The user request this run is executing")
    workspace: str = Field("", description="Workspace the run targets; empty = the default")
    gating: RiskOperation | None = Field(None, description="The operation that reached the threshold (FR-12)")
    accumulated: list[RiskOperation] = Field(default_factory=list, description="Blast radius (FR-11)")
    decision: str = Field("ask", description="approve | decline | ask (FR-15)")
    reasoning: str = Field("", description="The checker's reasoning, recorded verbatim (FR-16)")
    source: str = Field(
        "default",
        description="Which party decided: judge | trust | precedent | filter | default | user (P8 v2.0.0)",
    )
    matched_precedent: str | None = Field(None, description="Precedent id that unlocked a skip (FR-17)")
    # Spec 011 FR-25 adds no new asking surface: an ask reaches the operator as the existing 008
    # approval card, answered on the existing POST /api/chat/interaction. These two ids are what
    # make that route reachable from a 409 — without them a machine caller would have a refusal and
    # no way to answer it.
    interaction_id: str | None = Field(
        None, description="The 008 approval card raised for this ask, if one could be raised (FR-25)"
    )
    conversation_id: str | None = Field(
        None, description="Conversation the card belongs to; answer it on /api/chat/interaction"
    )


class InteractionResponse(BaseModel):
    """The user's (or machine caller's) answer to a pending interaction (spec 008 FR-12/FR-16)."""

    workspace: str | None = Field(None, description="Workspace selector; omitted = default")
    conversation_id: str = Field(..., description="Conversation the interaction belongs to")
    interaction_id: str = Field(..., description="The interaction id being answered (FR-16)")
    choice: str = Field(
        ...,
        description="An option id to select/approve, 'decline' to refuse, or 'chat' for deep context (FR-7)",
        examples=["opt-1", "decline", "chat"],
    )


# --- sidebar: wiki tree / upload / sessions (feature 004-assistant-sidebar) --


class WikiNode(BaseModel):
    """One entry in the workspace's `vault/wiki/` tree (FR-8/FR-15). Navigation-only."""

    name: str = Field(..., description="Base name of the file or folder")
    path: str = Field(..., description="Path relative to wiki/ (posix)")
    type: str = Field(..., description="'dir' | 'file'")
    children: list["WikiNode"] = Field(default_factory=list, description="Child nodes for a dir")


class WikiTree(BaseModel):
    """The active workspace's `vault/wiki/` subtree, scoped strictly to vault/wiki/ (FR-10)."""

    workspace: str
    root: str = Field("vault/wiki", description="Root the paths are relative to")
    nodes: list[WikiNode] = Field(default_factory=list)


class UploadedFile(BaseModel):
    """Result of depositing one uploaded file into vault/raw/ then ingesting it (FR-12)."""

    filename: str
    raw_path: str = Field(..., description="Path of the stored original, relative to the workspace")
    source_page: str | None = Field(None, description="vault/wiki/sources page produced by ingest, if any")
    ingested: bool = Field(False, description="Whether the file's text was ingested into vault/wiki/")
    error: str | None = Field(None, description="Populated when the file was stored but not ingested")


class UploadReport(BaseModel):
    """Outcome of an upload batch (FR-12/FR-13/FR-16)."""

    workspace: str
    files: list[UploadedFile] = Field(default_factory=list)
    count: int = Field(0, description="Number of files processed")
    committed: bool = Field(False, description="Whether the deposit was recorded as a git commit")


class ConversationMessage(BaseModel):
    role: str = Field(..., description="'user' | 'assistant'")
    text: str
    timestamp: str = ""


class ConversationSummary(BaseModel):
    """A prior conversation for the Sessions panel (FR-17/FR-19)."""

    conversation_id: str
    created: str
    title: str = Field(
        ...,
        description="The conversation's name, falling back to the first user line (spec 012 FR-10)",
    )
    turn_count: int = Field(0, description="Number of user turns")


class ConversationList(BaseModel):
    workspace: str
    conversations: list[ConversationSummary] = Field(default_factory=list)


class ConversationDetail(BaseModel):
    """Full turns of one conversation, to repopulate the chat on resume (FR-20)."""

    workspace: str
    conversation_id: str
    created: str
    title: str = Field(
        "",
        description="The conversation's name, falling back to the first user line "
        "(spec 004 FR-33, spec 012 FR-10)",
    )
    messages: list[ConversationMessage] = Field(default_factory=list)


# --- skills: catalog / installed / import (feature 005-skill-import) ---------


class SkillSummary(BaseModel):
    """One skill in the shared library catalog (spec 005 FR-2)."""

    name: str
    description: str = Field("", description="Short description parsed from SKILL.md frontmatter")
    installed: bool = Field(False, description="Whether it is reference-linked into the target workspace")


class SkillCatalog(BaseModel):
    """Available skills discovered under the shared library (spec 005 FR-2)."""

    source_root: str = Field(..., description="Resolved shared skill library root")
    skills: list[SkillSummary] = Field(default_factory=list)


class InstalledSkills(BaseModel):
    """A workspace's installed skill names (spec 005 FR-3)."""

    workspace: str
    skills: list[str] = Field(default_factory=list)


class ImportSkillRequest(BaseModel):
    """Reference-link a shared skill into a workspace (spec 005 FR-5)."""

    workspace: str | None = Field(None, description="Workspace selector; omitted = default")
    name: str = Field(..., description="Skill name in the shared library", examples=["weekly-digest"])


class ImportSkillReport(BaseModel):
    workspace: str
    name: str
    link_path: str = Field(..., description="Path of the created skills/<name> link, relative to the workspace")
    committed: bool = Field(..., description="Whether the install was recorded as a git commit")
    message: str


class ModelChoice(BaseModel):
    """One selectable Claude Agent SDK model (spec 004 FR-26/FR-27)."""

    id: str = Field(..., description="Model selector passed to the SDK (alias or full id)")
    label: str = Field(..., description="Human-readable display name")
    description: str = Field("", description="Optional extra detail")


class AvailableModels(BaseModel):
    """The model picker's data: the list, the active choice, and where the list came from (FR-27)."""

    models: list[ModelChoice] = Field(default_factory=list)
    current: str = Field(..., description="The currently active model selector")
    source: str = Field(..., description="'provider' (fetched) | 'static' (offline fallback)")


class SetModelRequest(BaseModel):
    """Select the process-wide agent model (spec 004 FR-28)."""

    model: str = Field(..., description="Model selector to activate", examples=["opus"])


class Settings(BaseModel):
    """Operator-owned runtime settings, persisted across restarts (spec 009 FR-8)."""

    auto_approve: bool = Field(
        False, description="Trust mode: approval-tier actions run without a per-action prompt (FR-7/FR-8)"
    )
    agent_model: str = Field(..., description="The active agent model selector (spec 004 FR-28)")


class SettingsUpdate(BaseModel):
    """Update operator settings; omitted fields are left unchanged (spec 009 FR-8)."""

    auto_approve: bool | None = Field(None, description="New trust-mode value", examples=[True])


# ChatAnswer/ChatDelta forward-reference Interaction (defined below them); resolve now.
ChatAnswer.model_rebuild()
ChatDelta.model_rebuild()
