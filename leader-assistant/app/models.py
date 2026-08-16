"""Request/response models for the capability layer and REST surface.

These are the JSON contracts shown in Swagger. Kept surface-agnostic so
chat and REST share identical shapes (Constitution P9, spec 13-api).
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class VaultList(BaseModel):
    root: str = Field(..., description="Resolved vault root directory")
    vaults: list[str] = Field(default_factory=list, description="Scaffolded vault names")
    default: str = Field(..., description="Default vault selector")


class CreateVaultRequest(BaseModel):
    name: str = Field(..., description="Vault name to create under the root", examples=["default"])


class VaultInfo(BaseModel):
    name: str
    path: str
    scaffolded: bool
    pages: int = Field(0, description="Count of Markdown pages under wiki/")


class IngestRequest(BaseModel):
    vault: str | None = Field(None, description="Vault selector; omitted = default")
    title: str = Field(..., description="Human title of the source", examples=["Team sync notes"])
    content: str = Field(..., description="Raw Markdown/text content to ingest")
    provenance: str = Field(
        "notes",
        description="raw/ subfolder signalling source type",
        examples=["notes", "clippings", "docs", "transcripts"],
    )


class IngestReport(BaseModel):
    vault: str
    source_page: str = Field(..., description="Path of the created wiki/sources summary")
    portal_updated: bool
    committed: bool = Field(..., description="Whether a git commit was recorded")
    message: str


class QueryRequest(BaseModel):
    vault: str | None = Field(None, description="Vault selector; omitted = default")
    question: str = Field(..., description="Natural-language question", examples=["What decisions were made?"])


class Citation(BaseModel):
    page: str
    excerpt: str


class Answer(BaseModel):
    vault: str
    question: str
    answer: str
    citations: list[Citation] = Field(default_factory=list)


class PlanRequest(BaseModel):
    vault: str | None = None
    request: str = Field(..., description="Work request to plan", examples=["Refactor onboarding docs"])


class PlanStep(BaseModel):
    order: int
    action: str
    rationale: str


class Plan(BaseModel):
    vault: str
    request: str
    steps: list[PlanStep]
    risk: str = Field(..., description="Risk outcome: safe | risky | reject")
    requires_approval: bool = Field(
        ..., description="Consequential work returns a plan for approval, never silent execution (spec 13-api AC2)"
    )


class LintFinding(BaseModel):
    kind: str = Field(..., description="orphan | stale | contradiction | missing")
    page: str
    detail: str


class LintReport(BaseModel):
    vault: str
    findings: list[LintFinding] = Field(default_factory=list)
    ok: bool


# --- chat (feature 002-assistant-chat) -------------------------------------


class ChatRequest(BaseModel):
    """A single chat turn (spec 002 plan Data Contracts)."""

    message: str = Field(..., description="User message for this turn", examples=["What does the risk engine decide?"])
    vault: str | None = Field(None, description="Vault selector; omitted = default (P13)")
    conversation_id: str | None = Field(
        None, description="Resume a prior conversation; omitted = start a new one (FR-3)"
    )
    approve: bool = Field(
        False, description="Approve the conversation's pending plan and execute it (FR-5, D2)"
    )


class ChatAnswer(BaseModel):
    """Full (non-streamed) reply for a chat turn (FR-1)."""

    vault: str
    conversation_id: str = Field(..., description="Durable id; resend to continue the thread (FR-3, FR-13)")
    reply: str
    citations: list[Citation] = Field(default_factory=list, description="Vault pages supporting the reply (FR-2)")
    pending_plan: Plan | None = Field(
        None, description="Populated when the request is consequential and awaits approval (FR-5)"
    )
    executed: bool = Field(False, description="True when this turn approved and executed a stored plan (FR-5)")


class ChatDelta(BaseModel):
    """One streamed chunk; the final delta carries done=true (FR-4)."""

    vault: str
    conversation_id: str
    reply: str = Field(..., description="Accumulated reply so far")
    done: bool = Field(False, description="True on the final event")
    citations: list[Citation] = Field(default_factory=list)
    pending_plan: Plan | None = None
    executed: bool = False


# --- sidebar: wiki tree / upload / sessions (feature 004-assistant-sidebar) --


class WikiNode(BaseModel):
    """One entry in the vault's `wiki/` tree (FR-8/FR-15). Navigation-only."""

    name: str = Field(..., description="Base name of the file or folder")
    path: str = Field(..., description="Path relative to wiki/ (posix)")
    type: str = Field(..., description="'dir' | 'file'")
    children: list["WikiNode"] = Field(default_factory=list, description="Child nodes for a dir")


class WikiTree(BaseModel):
    """The active vault's `wiki/` subtree, scoped strictly to wiki/ (FR-10)."""

    vault: str
    root: str = Field("wiki", description="Root the paths are relative to")
    nodes: list[WikiNode] = Field(default_factory=list)


class UploadedFile(BaseModel):
    """Result of depositing one uploaded file into raw/ then ingesting it (FR-12)."""

    filename: str
    raw_path: str = Field(..., description="Path of the stored original, relative to the vault")
    source_page: str | None = Field(None, description="wiki/sources page produced by ingest, if any")
    ingested: bool = Field(False, description="Whether the file's text was ingested into wiki/")
    error: str | None = Field(None, description="Populated when the file was stored but not ingested")


class UploadReport(BaseModel):
    """Outcome of an upload batch (FR-12/FR-13/FR-16)."""

    vault: str
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
    title: str = Field(..., description="Derived label (first user message, truncated)")
    turn_count: int = Field(0, description="Number of user turns")


class ConversationList(BaseModel):
    vault: str
    conversations: list[ConversationSummary] = Field(default_factory=list)


class ConversationDetail(BaseModel):
    """Full turns of one conversation, to repopulate the chat on resume (FR-20)."""

    vault: str
    conversation_id: str
    created: str
    messages: list[ConversationMessage] = Field(default_factory=list)
