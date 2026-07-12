"""Gradio UI for the Leader Assistant - an IM-style chat interface."""
import argparse
import logging
import os
import warnings

warnings.filterwarnings("ignore", message=r".*HTTP_422_UNPROCESSABLE_ENTITY.*")

import gradio as gr

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


def launch(debug: bool = False, **kwargs):
    """Build and launch the app."""
    if debug:
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
    return build_demo().launch(css=CSS, head=HEAD, theme=gr.themes.Base(), **kwargs)


def main():
    parser = argparse.ArgumentParser(description="Leader Assistant server")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    parser.add_argument("--port", type=int, default=7860, help="Server port")
    parser.add_argument("--share", action="store_true", help="Create public URL")
    args = parser.parse_args()

    print(f"Starting Leader Assistant: port={args.port}, debug={args.debug}, share={args.share}", flush=True)
    launch(debug=args.debug, server_port=args.port, share=args.share)


if __name__ == "__main__":
    main()
