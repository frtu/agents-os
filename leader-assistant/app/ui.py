"""Gradio web UI — the human startup surface (feature 003-assistant-ui).

The UI is a *pure presentation layer*: it reaches the vault only by calling the
backend REST API over HTTP (same origin), never `app.capabilities` / `app.vault`
directly (spec 003 FR-3/AC-8, Constitution P9). It is mounted on the FastAPI app
at `/` (see `app/api.py`); Swagger lives at `/api/`.

Chat streams from `POST /api/chat/stream` (SSE) with a full-reply fallback to
`POST /api/chat`; vaults come from `/api/vaults`. Consequential replies carry a
`pending_plan` which the UI shows with an explicit **Approve plan** control
(spec 003 FR-8, P8) — no auto-approval.
"""

from __future__ import annotations

import json
import os

import gradio as gr
import httpx

THINKING = '<span class="thinking">…thinking…</span>'
GREETING = (
    "Hi — I'm your project's Product Owner assistant. Pick a vault, then ask me "
    "anything about the project. I answer from the vault with citations."
)
APPROVE_MSG = "Approve the pending plan and execute it."


def _api_base() -> str:
    """Base URL of our own REST API (same process/port as this UI)."""
    override = os.getenv("LEADER_API_BASE")
    if override:
        return override.rstrip("/")
    host = os.getenv("LEADER_HOST", "127.0.0.1")
    if host == "0.0.0.0":
        host = "127.0.0.1"
    port = os.getenv("LEADER_PORT", "8000")
    return f"http://{host}:{port}"


# --- REST API client helpers (UI -> /api/* over HTTP only) -----------------


def _list_vaults() -> dict:
    r = httpx.get(f"{_api_base()}/api/vaults", timeout=10.0)
    r.raise_for_status()
    return r.json()


def _create_vault(name: str) -> dict:
    r = httpx.post(f"{_api_base()}/api/vaults", json={"name": name}, timeout=30.0)
    r.raise_for_status()
    return r.json()


async def _stream_chat(vault, message, conversation_id, approve):
    """Yield decoded ChatDelta dicts from the SSE chat stream.

    Emits a single ``{"error": ...}`` dict on a non-2xx response so callers can
    surface it to the user (FR-11) instead of failing silently.
    """
    payload = {
        "message": message,
        "vault": vault or None,
        "conversation_id": conversation_id,
        "approve": approve,
    }
    async with httpx.AsyncClient(base_url=_api_base(), timeout=httpx.Timeout(None)) as c:
        async with c.stream("POST", "/api/chat/stream", json=payload) as r:
            if r.status_code != 200:
                body = (await r.aread()).decode(errors="replace")[:300]
                yield {"error": f"API {r.status_code}: {body}"}
                return
            async for line in r.aiter_lines():
                line = line.strip()
                if line.startswith("data:"):
                    try:
                        yield json.loads(line[len("data:"):].strip())
                    except json.JSONDecodeError:
                        continue


# --- rendering helpers ------------------------------------------------------


def _format_extras(citations, pending_plan) -> str:
    parts: list[str] = []
    if citations:
        parts.append("\n\n**Sources**")
        for c in citations:
            parts.append(f"- `{c.get('page','?')}` — {c.get('excerpt','')}")
    if pending_plan:
        parts.append(f"\n\n**Plan awaiting approval** (risk: {pending_plan.get('risk','?')})")
        for s in pending_plan.get("steps", []):
            parts.append(f"{s.get('order','?')}. {s.get('action','')} — {s.get('rationale','')}")
        parts.append("\n_Click **Approve plan** below to execute — nothing changes until you do._")
    return "\n".join(parts)


# --- Gradio event handlers --------------------------------------------------


def _text(content) -> str:
    """Flatten Gradio chat content (str or list of {text,type} parts) to a string."""
    if isinstance(content, list):
        return " ".join(
            p.get("text", "") for p in content if isinstance(p, dict)
        ).strip()
    return content or ""


def _user_submit(msg, history):
    msg = (msg or "").strip()
    if not msg:
        return "", history or []
    return "", (history or []) + [{"role": "user", "content": msg}]


def _add_approve_msg(history):
    return (history or []) + [{"role": "user", "content": APPROVE_MSG}]


async def _run_turn(history, conversation_id, vault, approve):
    """Stream one assistant turn, updating the last message as text arrives."""
    user_msg = _text(history[-1]["content"]) if history else ""
    history = history + [{"role": "assistant", "content": THINKING}]
    yield history, conversation_id, gr.update(visible=False)

    reply, cid = "", conversation_id
    citations, pending = [], None
    try:
        async for data in _stream_chat(vault, user_msg, conversation_id, approve):
            if "error" in data:
                history[-1]["content"] = f"⚠️ {data['error']}"
                yield history, cid, gr.update(visible=False)
                return
            reply = data.get("reply", reply)
            cid = data.get("conversation_id", cid)
            citations = data.get("citations") or citations
            pending = data.get("pending_plan") or pending
            history[-1]["content"] = reply or THINKING
            yield history, cid, gr.update(visible=False)
    except Exception as e:  # network/transport failure -> surface it (FR-11)
        history[-1]["content"] = f"⚠️ Could not reach the API: {e}"
        yield history, cid, gr.update(visible=False)
        return

    history[-1]["content"] = (reply or "…") + _format_extras(citations, pending)
    yield history, cid, gr.update(visible=bool(pending))


async def _respond(history, conversation_id, vault):
    async for out in _run_turn(history, conversation_id, vault, approve=False):
        yield out


async def _approve(history, conversation_id, vault):
    async for out in _run_turn(history, conversation_id, vault, approve=True):
        yield out


def _refresh_vaults(current):
    try:
        info = _list_vaults()
    except Exception as e:
        return gr.update(), current, f"Could not list vaults: {e}"
    vaults = info.get("vaults", [])
    default = info.get("default", "default")
    value = current if current in vaults else (
        default if default in vaults else (vaults[0] if vaults else None)
    )
    return gr.update(choices=vaults, value=value), value, ""


def _create_vault_action(name, current):
    name = (name or "").strip()
    if not name:
        return gr.update(), current, "", "Enter a vault name to create."
    try:
        _create_vault(name)
    except Exception as e:
        return gr.update(), current, name, f"Could not create vault: {e}"
    try:
        vaults = _list_vaults().get("vaults", [])
    except Exception:
        vaults = [name]
    return gr.update(choices=vaults, value=name), name, "", f"Created vault '{name}'."


# --- UI assembly ------------------------------------------------------------


def build_demo() -> gr.Blocks:
    with gr.Blocks(title="Leader Assistant") as demo:
        gr.HTML('<h2 style="margin:8px 2px">Leader <b>Assistant</b></h2>')
        conversation = gr.State(None)
        active_vault = gr.State(None)

        with gr.Row():
            vault_dd = gr.Dropdown(label="Vault", choices=[], interactive=True, scale=3)
            refresh_btn = gr.Button("↻ Refresh", scale=1)
        with gr.Row():
            new_vault = gr.Textbox(label="New vault name", scale=3, placeholder="e.g. project-x")
            create_btn = gr.Button("Create vault", scale=1)
        status = gr.Markdown("")

        chat = gr.Chatbot(
            height=520,
            show_label=False,
            value=[{"role": "assistant", "content": GREETING}],
        )
        box = gr.Textbox(
            show_label=False,
            submit_btn=True,
            placeholder="Ask about the project…",
        )
        approve_btn = gr.Button("✅ Approve plan", variant="primary", visible=False)

        # Populate the vault picker once the page loads (server is up by then).
        demo.load(_refresh_vaults, [active_vault], [vault_dd, active_vault, status])
        refresh_btn.click(_refresh_vaults, [active_vault], [vault_dd, active_vault, status])
        vault_dd.change(lambda v: v, [vault_dd], [active_vault])
        create_btn.click(
            _create_vault_action,
            [new_vault, active_vault],
            [vault_dd, active_vault, new_vault, status],
        )

        box.submit(_user_submit, [box, chat], [box, chat]).then(
            _respond, [chat, conversation, active_vault], [chat, conversation, approve_btn]
        )
        approve_btn.click(_add_approve_msg, [chat], [chat]).then(
            _approve, [chat, conversation, active_vault], [chat, conversation, approve_btn]
        )

    return demo
