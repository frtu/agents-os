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
