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
from fastapi.responses import JSONResponse, StreamingResponse

from . import capabilities, concierge, models, tracing
from .vault import WorkspaceError

app = FastAPI(
    title="Leader Assistant API",
    version="0.1.0",
    description=(
        "Machine-facing surface over the shared capability layer.\n\n"
        "Every capability is a plain function in `app.capabilities`, and every route reaches it "
        "through the **concierge** (spec 011 FR-23) — the same entry point chat uses, so both "
        "surfaces reach the same verdict for the same request. Each operation is announced with "
        "its declared effect, scored 1–5, and judged against everything the request has already "
        "done. Low-risk work runs immediately (reversible effects are git-committed, so they are "
        "undoable). Work that reaches the review threshold returns **409** with a "
        "`RiskAssessment`: the accumulated list of operations, each with its score and a one-line "
        "justification. Standing consent is the operator's to grant (`auto_approve`, "
        "`/api/settings`), never the agent's. Interactive docs: **/api/**; the web UI is at **/**."
    ),
    contact={"name": "Leader Assistant", "url": "https://example.local"},
    docs_url="/api",  # Swagger UI at /api/ — the web UI owns / (spec 003 D4/FR-2)
)


@app.exception_handler(concierge.ApprovalRequired)
async def _approval_required(_request, exc: concierge.ApprovalRequired) -> JSONResponse:
    """A paused run, rendered for a machine caller (spec 011 FR-25).

    409 Conflict, not 403: the request is well-formed and permitted in principle, it simply cannot
    proceed until the operator decides. The body is the whole accumulated assessment, because the
    caller needs the blast radius to decide, not just the refusal.
    """
    return JSONResponse(status_code=409, content=exc.assessment.model_dump())


@app.exception_handler(concierge.Declined)
async def _declined(_request, exc: concierge.Declined) -> JSONResponse:
    """A refusal. Decline is decline (spec 011 FR-27) — 403, with the reasoning that produced it."""
    return JSONResponse(status_code=403, content=exc.assessment.model_dump())


@app.get("/health", tags=["ops"], summary="Liveness probe")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.on_event("shutdown")
async def _flush_traces() -> None:
    """Best-effort send of buffered Langfuse spans on a graceful shutdown (spec 013 FR-6)."""
    tracing.flush()


# Every route below reaches a capability through `concierge.invoke` (spec 011 FR-23), never
# directly. It is uniform on purpose: a read scores 1 and passes without ever waking the judge, so
# the ceremony is nearly free, and being uniform is what makes "no surface may reach execution
# directly" a property of the file rather than a habit of whoever wrote the last route.


@app.get("/api/workspaces", response_model=models.WorkspaceList, tags=["workspace"], summary="List workspaces")
async def list_workspaces() -> models.WorkspaceList:
    return await concierge.invoke("list_workspaces", "", capabilities.list_workspaces)


@app.post("/api/workspaces", response_model=models.WorkspaceInfo, tags=["workspace"], summary="Create/scaffold a workspace")
async def create_workspace(req: models.CreateWorkspaceRequest) -> models.WorkspaceInfo:
    """Scaffold a workspace. An `approval`-tier effect: no revert in any existing workspace removes
    it, so it is judged before it runs and may return 409 (spec 011 FR-25)."""
    return await concierge.invoke(
        "create_workspace", req.name, lambda: capabilities.create_workspace(req.name),
        objective=f"create workspace {req.name}",
    )


@app.get("/api/workspaces/{selector}", response_model=models.WorkspaceInfo, tags=["workspace"], summary="Inspect a workspace")
async def workspace_info(selector: str) -> models.WorkspaceInfo:
    return await concierge.invoke(
        "get_workspace_info", selector, lambda: capabilities.get_workspace_info(selector),
        workspace=selector,
    )


@app.post("/api/ingest", response_model=models.IngestReport, tags=["knowledge"], summary="Ingest a source")
async def ingest(req: models.IngestRequest) -> models.IngestReport:
    try:
        return await concierge.invoke(
            "ingest", req.title, lambda: capabilities.ingest(req),
            workspace=req.workspace or "", objective=f"ingest {req.title}",
        )
    except WorkspaceError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/query", response_model=models.Answer, tags=["knowledge"], summary="Query the workspace (cited)")
async def query(req: models.QueryRequest) -> models.Answer:
    return await concierge.invoke(
        "query", req.question, lambda: capabilities.query(req), workspace=req.workspace or "",
    )


@app.post("/api/plan", response_model=models.Plan, tags=["governance"], summary="Plan consequential work")
async def plan(req: models.PlanRequest) -> models.Plan:
    return await concierge.invoke(
        "plan", req.request, lambda: capabilities.plan(req), workspace=req.workspace or "",
    )


@app.get("/api/lint", response_model=models.LintReport, tags=["ops"], summary="Lint a workspace")
async def lint(workspace: str | None = None) -> models.LintReport:
    return await concierge.invoke(
        "lint", workspace or "", lambda: capabilities.lint(workspace), workspace=workspace or "",
    )


@app.get("/api/models", response_model=models.AvailableModels, tags=["ops"], summary="List selectable agent models")
async def list_models() -> models.AvailableModels:
    """Available Claude Agent SDK models + the active one (spec 004 FR-26/FR-27)."""
    return await concierge.invoke("available_models", "", capabilities.available_models)


@app.post("/api/models", response_model=models.AvailableModels, tags=["ops"], summary="Select the process-wide agent model")
async def set_model(req: models.SetModelRequest) -> models.AvailableModels:
    """Select + persist the process-wide agent model (spec 004 FR-28)."""
    try:
        return await concierge.invoke(
            "set_active_model", req.model, lambda: capabilities.set_active_model(req.model),
        )
    except WorkspaceError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/settings", response_model=models.Settings, tags=["ops"], summary="Read operator settings")
async def get_settings() -> models.Settings:
    """The persisted operator settings, incl. trust mode (spec 009 FR-8)."""
    return await concierge.invoke("get_settings", "", capabilities.get_settings)


@app.post("/api/settings", response_model=models.Settings, tags=["ops"], summary="Update operator settings")
async def update_settings(req: models.SettingsUpdate) -> models.Settings:
    """Persist operator settings (spec 009 FR-8). Trust mode is operator-only — the agent has no
    tool for this route (FR-11), and no judge or precedent may write it (spec 011 FR-22)."""
    return await concierge.invoke(
        "update_settings", "auto_approve", lambda: capabilities.update_settings(req.auto_approve),
    )


@app.get("/api/spec", tags=["knowledge"], summary="Read a page's raw Markdown")
async def spec_read(path: str, workspace: str | None = None) -> dict[str, str]:
    try:
        content = await concierge.invoke(
            "spec_read", path, lambda: capabilities.spec_read(path, workspace),
            workspace=workspace or "",
        )
        return {"path": path, "content": content}
    except WorkspaceError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.get("/api/wiki-tree", response_model=models.WikiTree, tags=["knowledge"], summary="Browse the workspace's vault/wiki/ tree")
async def wiki_tree(workspace: str | None = None) -> models.WikiTree:
    """Navigation-only tree of the workspace's `vault/wiki/`, for the sidebar browser (spec 004 FR-8/FR-15)."""
    return await concierge.invoke(
        "wiki_tree", workspace or "", lambda: capabilities.wiki_tree(workspace),
        workspace=workspace or "",
    )


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
    names = ", ".join(name for name, _ in payload)
    try:
        return await concierge.invoke(
            "upload_and_ingest", names,
            lambda: capabilities.upload_and_ingest(workspace, payload, provenance),
            workspace=workspace or "", objective=f"upload {len(payload)} file(s) as {provenance}",
        )
    except WorkspaceError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/sessions", response_model=models.ConversationList, tags=["chat"], summary="List prior conversations")
async def sessions(workspace: str | None = None) -> models.ConversationList:
    """Prior conversations for the Sessions panel (spec 004 FR-17/FR-19)."""
    return await concierge.invoke(
        "list_conversations", workspace or "", lambda: capabilities.list_conversations(workspace),
        workspace=workspace or "",
    )


@app.get("/api/sessions/{conversation_id}", response_model=models.ConversationDetail, tags=["chat"], summary="Read one conversation's turns")
async def session_detail(conversation_id: str, workspace: str | None = None) -> models.ConversationDetail:
    """Full turns of one conversation, to repopulate the chat on resume (spec 004 FR-20)."""
    try:
        return await concierge.invoke(
            "get_conversation", conversation_id,
            lambda: capabilities.get_conversation(workspace, conversation_id),
            workspace=workspace or "",
        )
    except WorkspaceError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.get("/api/chat/status", response_model=models.ChatStatus, tags=["chat"], summary="Is a conversation still running?")
async def chat_status(conversation_id: str, workspace: str | None = None) -> models.ChatStatus:
    """Report whether a conversation has a turn in-flight on the server (spec 002 FR-14).

    Read-only probe — it never sends a turn or mutates the record. An unknown id returns
    `running=false, exists=false`.
    """
    return await concierge.invoke(
        "conversation_status", conversation_id,
        lambda: capabilities.conversation_status(workspace, conversation_id),
        workspace=workspace or "",
    )


@app.post("/api/chat", response_model=models.ChatAnswer, tags=["chat"], summary="Chat with the Product Owner")
async def chat(req: models.ChatRequest) -> models.ChatAnswer:
    """Hold a durable, resumable conversation with the assistant (spec 14-chat).

    Same capability layer as REST (P9). A turn is gated only when an executable
    `approval`-tier capability is about to run (spec 009 FR-3); `auto_approve` grants
    standing consent for this turn (FR-7/FR-9).
    """
    try:
        return await concierge.chat(
            req.workspace, req.message, req.conversation_id, req.approve, req.auto_approve
        )
    except WorkspaceError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/chat/stream", tags=["chat"], summary="Chat (streamed, SSE)")
async def chat_stream(req: models.ChatRequest) -> StreamingResponse:
    """Server-Sent Events stream of the reply; the final event has `done: true` (FR-4)."""

    async def events():
        try:
            async for delta in concierge.chat_stream(
                req.workspace, req.message, req.conversation_id, req.approve, req.auto_approve
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
async def get_interaction(conversation_id: str, workspace: str | None = None) -> models.Interaction | None:
    """Return the still-pending interaction for a conversation, or null (spec 008 FR-11).

    Lets a reloaded/reconnected client re-render an unanswered approval/clarification card. An
    elapsed interaction is auto-resolved to its safe default and returned with status='expired'.
    """
    return await concierge.invoke(
        "get_pending_interaction", conversation_id,
        lambda: capabilities.get_pending_interaction(workspace, conversation_id),
        workspace=workspace or "",
    )


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
        return await concierge.respond(
            req.workspace, req.conversation_id, req.interaction_id, req.choice
        )
    except WorkspaceError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/chat/interaction/stream", tags=["chat"], summary="Respond to a pending interaction (streamed, SSE)")
async def respond_interaction_stream(req: models.InteractionResponse) -> StreamingResponse:
    """SSE stream of the resumed turn after answering an interaction; final event has `done: true`."""

    async def events():
        try:
            async for delta in concierge.respond_stream(
                req.workspace, req.conversation_id, req.interaction_id, req.choice
            ):
                yield f"data: {delta.model_dump_json()}\n\n"
        except WorkspaceError as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(events(), media_type="text/event-stream")


# --- skills (feature 005-skill-import; parity, P9) --------------------------


@app.get("/api/skills", response_model=models.SkillCatalog, tags=["skills"], summary="List available skills in the shared library")
async def skills_catalog(workspace: str | None = None) -> models.SkillCatalog:
    """Catalog the shared skill library, marking which are installed in the workspace (spec 005 FR-2)."""
    return await concierge.invoke(
        "list_available_skills", workspace or "",
        lambda: capabilities.list_available_skills(workspace),
        workspace=workspace or "",
    )


@app.get("/api/skills/installed", response_model=models.InstalledSkills, tags=["skills"], summary="List a workspace's installed skills")
async def skills_installed(workspace: str | None = None) -> models.InstalledSkills:
    """Installed skill names for a workspace (spec 005 FR-3)."""
    return await concierge.invoke(
        "list_installed_skills", workspace or "",
        lambda: capabilities.list_installed_skills(workspace),
        workspace=workspace or "",
    )


@app.post("/api/skills/import", response_model=models.ImportSkillReport, tags=["skills"], summary="Reference-link a skill into a workspace")
async def skills_import(req: models.ImportSkillRequest) -> models.ImportSkillReport:
    """Import a shared skill as a reference-link (spec 005 FR-5).

    An `approval`-tier effect: installing a skill grants the agent new executable behaviour, so it
    is judged before it runs and may return 409 with the accumulated assessment (spec 011 FR-25).
    """
    try:
        # Bad input is answered as bad input, before anyone is asked to approve an impossible
        # install: an unknown or malformed skill name is 400, not a risk decision.
        capabilities.resolve_skill_source(req.name)
        return await concierge.invoke(
            "import_skill", req.name, lambda: capabilities.import_skill(req.workspace, req.name),
            workspace=req.workspace or "", objective=f"install skill {req.name}",
        )
    except WorkspaceError as e:
        raise HTTPException(status_code=400, detail=str(e))


# --- human web UI (spec 003-assistant-ui) ----------------------------------
# Mount the Gradio startup surface at `/`. Registered last so the explicit REST
# routes above (and Swagger at /api/) take precedence; Gradio serves its own
# assets under /gradio_api/, so it does not shadow /api/<resource> (FR-1, FR-2).
import gradio as gr  # noqa: E402  (heavy import; kept local to app startup)

from .ui import build_demo  # noqa: E402

app = gr.mount_gradio_app(app, build_demo(), path="/")
