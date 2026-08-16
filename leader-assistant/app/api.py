"""REST surface over the capability layer (FastAPI).

FastAPI auto-generates the OpenAPI schema and serves the interactive Swagger UI.
Per spec 003-assistant-ui (D4/FR-2) the human web UI owns the root path `/`, so
Swagger is relocated to **/api/** (`docs_url="/api"`); the OpenAPI schema stays at
`/openapi.json` and ReDoc at `/redoc`. The Gradio UI is mounted at `/` at the end
of this module. This surface must stay in capability parity with any chat surface
(Constitution P9, spec 13-api).
"""

from __future__ import annotations

import json

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse

from . import capabilities, models
from .vault import VaultError

app = FastAPI(
    title="Leader Assistant API",
    version="0.1.0",
    description=(
        "Machine-facing surface over the shared capability layer.\n\n"
        "Every capability is a plain function in `app.capabilities`; "
        "consequential requests return a **plan** for approval rather than executing "
        "silently (spec 13-api AC2). Interactive docs: **/api/**; the web UI is at **/**."
    ),
    contact={"name": "Leader Assistant", "url": "https://example.local"},
    docs_url="/api",  # Swagger UI at /api/ — the web UI owns / (spec 003 D4/FR-2)
)


@app.get("/health", tags=["ops"], summary="Liveness probe")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/vaults", response_model=models.VaultList, tags=["vault"], summary="List vaults")
def list_vaults() -> models.VaultList:
    return capabilities.list_vaults()


@app.post("/api/vaults", response_model=models.VaultInfo, tags=["vault"], summary="Create/scaffold a vault")
def create_vault(req: models.CreateVaultRequest) -> models.VaultInfo:
    return capabilities.create_vault(req.name)


@app.get("/api/vaults/{selector}", response_model=models.VaultInfo, tags=["vault"], summary="Inspect a vault")
def vault_info(selector: str) -> models.VaultInfo:
    return capabilities.get_vault_info(selector)


@app.post("/api/ingest", response_model=models.IngestReport, tags=["knowledge"], summary="Ingest a source")
def ingest(req: models.IngestRequest) -> models.IngestReport:
    try:
        return capabilities.ingest(req)
    except VaultError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/query", response_model=models.Answer, tags=["knowledge"], summary="Query the vault (cited)")
def query(req: models.QueryRequest) -> models.Answer:
    return capabilities.query(req)


@app.post("/api/plan", response_model=models.Plan, tags=["governance"], summary="Plan consequential work")
def plan(req: models.PlanRequest) -> models.Plan:
    return capabilities.plan(req)


@app.get("/api/lint", response_model=models.LintReport, tags=["ops"], summary="Lint a vault")
def lint(vault: str | None = None) -> models.LintReport:
    return capabilities.lint(vault)


@app.get("/api/spec", tags=["knowledge"], summary="Read a page's raw Markdown")
def spec_read(path: str, vault: str | None = None) -> dict[str, str]:
    try:
        return {"path": path, "content": capabilities.spec_read(path, vault)}
    except VaultError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.get("/api/wiki-tree", response_model=models.WikiTree, tags=["knowledge"], summary="Browse the vault's wiki/ tree")
def wiki_tree(vault: str | None = None) -> models.WikiTree:
    """Navigation-only tree of the vault's `wiki/`, for the sidebar browser (spec 004 FR-8/FR-15)."""
    return capabilities.wiki_tree(vault)


@app.post("/api/upload", response_model=models.UploadReport, tags=["knowledge"], summary="Upload files into raw/ and ingest")
async def upload(
    vault: str | None = Form(None),
    provenance: str = Form("notes"),
    files: list[UploadFile] = File(...),
) -> models.UploadReport:
    """Deposit uploaded originals into `raw/<provenance>/` then ingest them (spec 004 FR-12/FR-16).

    `raw/` is human-owned (Constitution P2 v1.1.0); this is the sanctioned human upload channel.
    """
    payload = [(f.filename or "upload", await f.read()) for f in files]
    try:
        return capabilities.upload_and_ingest(vault, payload, provenance)
    except VaultError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/sessions", response_model=models.ConversationList, tags=["chat"], summary="List prior conversations")
def sessions(vault: str | None = None) -> models.ConversationList:
    """Prior conversations for the Sessions panel (spec 004 FR-17/FR-19)."""
    return capabilities.list_conversations(vault)


@app.get("/api/sessions/{conversation_id}", response_model=models.ConversationDetail, tags=["chat"], summary="Read one conversation's turns")
def session_detail(conversation_id: str, vault: str | None = None) -> models.ConversationDetail:
    """Full turns of one conversation, to repopulate the chat on resume (spec 004 FR-20)."""
    try:
        return capabilities.get_conversation(vault, conversation_id)
    except VaultError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.post("/api/chat", response_model=models.ChatAnswer, tags=["chat"], summary="Chat with the Product Owner")
async def chat(req: models.ChatRequest) -> models.ChatAnswer:
    """Hold a durable, resumable conversation with the assistant (spec 14-chat).

    Same capability layer as REST (P9): consequential requests return a
    `pending_plan` for approval and mutate nothing this turn (FR-5).
    """
    try:
        return await capabilities.ask(
            req.vault, req.message, req.conversation_id, req.approve
        )
    except VaultError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/chat/stream", tags=["chat"], summary="Chat (streamed, SSE)")
async def chat_stream(req: models.ChatRequest) -> StreamingResponse:
    """Server-Sent Events stream of the reply; the final event has `done: true` (FR-4)."""

    async def events():
        try:
            async for delta in capabilities.ask_stream(
                req.vault, req.message, req.conversation_id, req.approve
            ):
                yield f"data: {delta.model_dump_json()}\n\n"
        except VaultError as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(events(), media_type="text/event-stream")


# --- human web UI (spec 003-assistant-ui) ----------------------------------
# Mount the Gradio startup surface at `/`. Registered last so the explicit REST
# routes above (and Swagger at /api/) take precedence; Gradio serves its own
# assets under /gradio_api/, so it does not shadow /api/<resource> (FR-1, FR-2).
import gradio as gr  # noqa: E402  (heavy import; kept local to app startup)

from .ui import build_demo  # noqa: E402

app = gr.mount_gradio_app(app, build_demo(), path="/")
