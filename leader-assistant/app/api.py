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
from .vault import WorkspaceError

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


@app.get("/api/workspaces", response_model=models.WorkspaceList, tags=["workspace"], summary="List workspaces")
def list_workspaces() -> models.WorkspaceList:
    return capabilities.list_workspaces()


@app.post("/api/workspaces", response_model=models.WorkspaceInfo, tags=["workspace"], summary="Create/scaffold a workspace")
def create_workspace(req: models.CreateWorkspaceRequest) -> models.WorkspaceInfo:
    return capabilities.create_workspace(req.name)


@app.get("/api/workspaces/{selector}", response_model=models.WorkspaceInfo, tags=["workspace"], summary="Inspect a workspace")
def workspace_info(selector: str) -> models.WorkspaceInfo:
    return capabilities.get_workspace_info(selector)


@app.post("/api/ingest", response_model=models.IngestReport, tags=["knowledge"], summary="Ingest a source")
def ingest(req: models.IngestRequest) -> models.IngestReport:
    try:
        return capabilities.ingest(req)
    except WorkspaceError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/query", response_model=models.Answer, tags=["knowledge"], summary="Query the workspace (cited)")
def query(req: models.QueryRequest) -> models.Answer:
    return capabilities.query(req)


@app.post("/api/plan", response_model=models.Plan, tags=["governance"], summary="Plan consequential work")
def plan(req: models.PlanRequest) -> models.Plan:
    return capabilities.plan(req)


@app.get("/api/lint", response_model=models.LintReport, tags=["ops"], summary="Lint a workspace")
def lint(workspace: str | None = None) -> models.LintReport:
    return capabilities.lint(workspace)


@app.get("/api/models", response_model=models.AvailableModels, tags=["ops"], summary="List selectable agent models")
def list_models() -> models.AvailableModels:
    """Available Claude Agent SDK models + the active one (spec 004 FR-26/FR-27)."""
    return capabilities.available_models()


@app.post("/api/models", response_model=models.AvailableModels, tags=["ops"], summary="Select the process-wide agent model")
def set_model(req: models.SetModelRequest) -> models.AvailableModels:
    """Select + persist the process-wide agent model (spec 004 FR-28)."""
    try:
        return capabilities.set_active_model(req.model)
    except WorkspaceError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/spec", tags=["knowledge"], summary="Read a page's raw Markdown")
def spec_read(path: str, workspace: str | None = None) -> dict[str, str]:
    try:
        return {"path": path, "content": capabilities.spec_read(path, workspace)}
    except WorkspaceError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.get("/api/wiki-tree", response_model=models.WikiTree, tags=["knowledge"], summary="Browse the workspace's vault/wiki/ tree")
def wiki_tree(workspace: str | None = None) -> models.WikiTree:
    """Navigation-only tree of the workspace's `vault/wiki/`, for the sidebar browser (spec 004 FR-8/FR-15)."""
    return capabilities.wiki_tree(workspace)


@app.post("/api/upload", response_model=models.UploadReport, tags=["knowledge"], summary="Upload files into vault/raw/ and ingest")
async def upload(
    workspace: str | None = Form(None),
    provenance: str = Form("notes"),
    files: list[UploadFile] = File(...),
) -> models.UploadReport:
    """Deposit uploaded originals into `vault/raw/<provenance>/` then ingest them (spec 004 FR-12/FR-16).

    `vault/raw/` is human-owned (Constitution P2 v1.1.0); this is the sanctioned human upload channel.
    """
    payload = [(f.filename or "upload", await f.read()) for f in files]
    try:
        return capabilities.upload_and_ingest(workspace, payload, provenance)
    except WorkspaceError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/sessions", response_model=models.ConversationList, tags=["chat"], summary="List prior conversations")
def sessions(workspace: str | None = None) -> models.ConversationList:
    """Prior conversations for the Sessions panel (spec 004 FR-17/FR-19)."""
    return capabilities.list_conversations(workspace)


@app.get("/api/sessions/{conversation_id}", response_model=models.ConversationDetail, tags=["chat"], summary="Read one conversation's turns")
def session_detail(conversation_id: str, workspace: str | None = None) -> models.ConversationDetail:
    """Full turns of one conversation, to repopulate the chat on resume (spec 004 FR-20)."""
    try:
        return capabilities.get_conversation(workspace, conversation_id)
    except WorkspaceError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.get("/api/chat/status", response_model=models.ChatStatus, tags=["chat"], summary="Is a conversation still running?")
def chat_status(conversation_id: str, workspace: str | None = None) -> models.ChatStatus:
    """Report whether a conversation has a turn in-flight on the server (spec 002 FR-14).

    Read-only probe — it never sends a turn or mutates the record. An unknown id returns
    `running=false, exists=false`.
    """
    return capabilities.conversation_status(workspace, conversation_id)


@app.post("/api/chat", response_model=models.ChatAnswer, tags=["chat"], summary="Chat with the Product Owner")
async def chat(req: models.ChatRequest) -> models.ChatAnswer:
    """Hold a durable, resumable conversation with the assistant (spec 14-chat).

    Same capability layer as REST (P9): consequential requests return a
    `pending_plan` for approval and mutate nothing this turn (FR-5).
    """
    try:
        return await capabilities.ask(
            req.workspace, req.message, req.conversation_id, req.approve
        )
    except WorkspaceError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/chat/stream", tags=["chat"], summary="Chat (streamed, SSE)")
async def chat_stream(req: models.ChatRequest) -> StreamingResponse:
    """Server-Sent Events stream of the reply; the final event has `done: true` (FR-4)."""

    async def events():
        try:
            async for delta in capabilities.ask_stream(
                req.workspace, req.message, req.conversation_id, req.approve
            ):
                yield f"data: {delta.model_dump_json()}\n\n"
        except WorkspaceError as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(events(), media_type="text/event-stream")


# --- agent<->user interaction (feature 008; parity, P9) --------------------


@app.get(
    "/api/chat/interaction",
    response_model=models.Interaction | None,
    tags=["chat"],
    summary="Fetch a conversation's pending interaction",
)
def get_interaction(conversation_id: str, workspace: str | None = None) -> models.Interaction | None:
    """Return the still-pending interaction for a conversation, or null (spec 008 FR-11).

    Lets a reloaded/reconnected client re-render an unanswered approval/clarification card. An
    elapsed interaction is auto-resolved to its safe default and returned with status='expired'.
    """
    return capabilities.get_pending_interaction(workspace, conversation_id)


@app.post(
    "/api/chat/interaction",
    response_model=models.ChatAnswer,
    tags=["chat"],
    summary="Respond to a pending interaction",
)
async def respond_interaction(req: models.InteractionResponse) -> models.ChatAnswer:
    """Answer a pending interaction by id and resume the task (spec 008 FR-12/FR-16).

    Same protocol the UI uses (P9): `choice` is an option id, `decline`, or `chat`. Responding to
    an unknown/resolved/expired id is rejected with no side effects.
    """
    try:
        return await capabilities.respond_to_interaction(
            req.workspace, req.conversation_id, req.interaction_id, req.choice
        )
    except WorkspaceError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/chat/interaction/stream", tags=["chat"], summary="Respond to a pending interaction (streamed, SSE)")
async def respond_interaction_stream(req: models.InteractionResponse) -> StreamingResponse:
    """SSE stream of the resumed turn after answering an interaction; final event has `done: true`."""

    async def events():
        try:
            async for delta in capabilities.respond_to_interaction_stream(
                req.workspace, req.conversation_id, req.interaction_id, req.choice
            ):
                yield f"data: {delta.model_dump_json()}\n\n"
        except WorkspaceError as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(events(), media_type="text/event-stream")


# --- skills (feature 005-skill-import; parity, P9) --------------------------


@app.get("/api/skills", response_model=models.SkillCatalog, tags=["skills"], summary="List available skills in the shared library")
def skills_catalog(workspace: str | None = None) -> models.SkillCatalog:
    """Catalog the shared skill library, marking which are installed in the workspace (spec 005 FR-2)."""
    return capabilities.list_available_skills(workspace)


@app.get("/api/skills/installed", response_model=models.InstalledSkills, tags=["skills"], summary="List a workspace's installed skills")
def skills_installed(workspace: str | None = None) -> models.InstalledSkills:
    """Installed skill names for a workspace (spec 005 FR-3)."""
    return capabilities.list_installed_skills(workspace)


@app.post("/api/skills/import", response_model=models.ImportSkillReport, tags=["skills"], summary="Reference-link a skill into a workspace")
def skills_import(req: models.ImportSkillRequest) -> models.ImportSkillReport:
    """Import a shared skill as a reference-link (spec 005 FR-5). Chat import stays plan-first;
    this REST route installs directly for machine callers."""
    try:
        return capabilities.import_skill(req.workspace, req.name)
    except WorkspaceError as e:
        raise HTTPException(status_code=400, detail=str(e))


# --- human web UI (spec 003-assistant-ui) ----------------------------------
# Mount the Gradio startup surface at `/`. Registered last so the explicit REST
# routes above (and Swagger at /api/) take precedence; Gradio serves its own
# assets under /gradio_api/, so it does not shadow /api/<resource> (FR-1, FR-2).
import gradio as gr  # noqa: E402  (heavy import; kept local to app startup)

from .ui import build_demo  # noqa: E402

app = gr.mount_gradio_app(app, build_demo(), path="/")
