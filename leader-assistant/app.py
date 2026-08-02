"""Gradio UI + REST API for the Leader Assistant - an IM-style chat interface."""
import argparse
import json
import logging
import os
import warnings

warnings.filterwarnings("ignore", message=r".*HTTP_422_UNPROCESSABLE_ENTITY.*")

import gradio as gr
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

import core
from style import CSS, HEAD

logger = logging.getLogger("leader-assistant")

THINKING = '<span class="thinking"><i></i><i></i><i></i></span>'
GREETING = "Hi! I'm your project assistant. Ask me anything about the codebase and I'll search the documentation to help you."


def _text(content):
    """Extract text from Gradio message content."""
    if isinstance(content, list):
        return " ".join(p.get("text", "") for p in content if isinstance(p, dict)).strip()
    return content or ""


def user_submit(msg, history):
    """Show the user's message immediately and clear the input box."""
    msg = (msg or "").strip()
    if not msg:
        return "", history or []
    return "", (history or []) + [{"role": "user", "content": msg}]


async def bot_respond(history, session_id):
    """Stream the assistant's reply."""
    user_msg = _text(history[-1]["content"])
    logger.debug(f"[REQUEST] session={session_id}\n{user_msg}")

    history = history + [{"role": "assistant", "content": THINKING}]
    yield history, session_id

    reply, sid = "", session_id
    async for reply, sid in core.stream_reply(user_msg, session_id):
        history[-1]["content"] = reply
        yield history, sid

    reply = reply or "I couldn't find relevant information. Could you rephrase your question?"
    history[-1]["content"] = reply
    logger.debug(f"[RESPONSE] session={sid}\n{reply}")
    yield history, sid


def build_demo():
    with gr.Blocks(title="Leader Assistant") as demo:
        gr.HTML('<div id="app_title">Leader <b>Assistant</b></div>')
        session = gr.State(None)

        with gr.Row():
            with gr.Column(scale=1):
                chat = gr.Chatbot(
                    elem_id="chat",
                    height=600,
                    show_label=False,
                    value=[{"role": "assistant", "content": GREETING}],
                )
                box = gr.Textbox(
                    elem_id="msgbox",
                    show_label=False,
                    submit_btn=True,
                    placeholder="Ask a question about the project...",
                )

        box.submit(user_submit, [box, chat], [box, chat]).then(
            bot_respond, [chat, session], [chat, session]
        )

    return demo


class AgentRequest(BaseModel):
    message: str
    session_id: str | None = None


class AgentResponse(BaseModel):
    reply: str
    session_id: str | None = None


def build_api() -> FastAPI:
    """Build the FastAPI app exposing REST endpoints for the skilled agent."""
    api = FastAPI(title="Leader Assistant API")

    # Allow browser clients (e.g. the leader-control-center frontend) to call
    # the REST API directly when not going through a same-origin proxy.
    api.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @api.get("/api/health")
    def health():
        return {"status": "ok"}

    @api.get("/api/skills")
    def skills():
        """List available and installed skills the agent can use."""
        return core.list_skills()

    @api.post("/api/agent", response_model=AgentResponse)
    async def run_agent(req: AgentRequest):
        """Trigger the agent (with its skills) and return the full reply."""
        logger.debug(f"[API] agent session={req.session_id}\n{req.message}")
        reply, sid = await core.get_reply(req.message, req.session_id)
        return AgentResponse(reply=reply, session_id=sid)

    @api.post("/api/agent/stream")
    async def run_agent_stream(req: AgentRequest):
        """Trigger the agent and stream the reply as Server-Sent Events."""
        logger.debug(f"[API] agent/stream session={req.session_id}\n{req.message}")

        async def events():
            reply, sid = "", req.session_id
            async for reply, sid in core.stream_reply(req.message, req.session_id):
                data = json.dumps({"reply": reply, "session_id": sid})
                yield f"data: {data}\n\n"
            done = json.dumps({"reply": reply, "session_id": sid, "done": True})
            yield f"data: {done}\n\n"

        return StreamingResponse(events(), media_type="text/event-stream")

    return api


def build_app() -> FastAPI:
    """Mount the Gradio UI onto the FastAPI app so both share one server."""
    api = build_api()
    demo = build_demo()
    return gr.mount_gradio_app(api, demo, path="/")


def _enable_debug_logging():
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(
        "%(asctime)s %(levelname)s %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    ))
    for name in ("leader-assistant", "leader-assistant.core"):
        log = logging.getLogger(name)
        log.setLevel(logging.DEBUG)
        log.addHandler(handler)
    logger.info("Debug mode enabled - logging all requests and responses")


def launch(debug: bool = False, host: str = "0.0.0.0", port: int = 7860):
    """Build the combined UI + REST app and serve it with uvicorn."""
    if debug:
        _enable_debug_logging()
    app = build_app()
    uvicorn.run(app, host=host, port=port)


def main():
    parser = argparse.ArgumentParser(description="Leader Assistant server")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    parser.add_argument("--host", default="0.0.0.0", help="Server host")
    parser.add_argument("--port", type=int, default=7860, help="Server port")
    args = parser.parse_args()

    print(f"Starting Leader Assistant: host={args.host}, port={args.port}, debug={args.debug}", flush=True)
    print(f"  UI:  http://localhost:{args.port}/", flush=True)
    print(f"  API: http://localhost:{args.port}/api/agent (POST), /api/skills (GET)", flush=True)
    launch(debug=args.debug, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
