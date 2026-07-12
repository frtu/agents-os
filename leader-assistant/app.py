"""Gradio UI for the Leader Assistant - an IM-style chat interface."""
import warnings

warnings.filterwarnings("ignore", message=r".*HTTP_422_UNPROCESSABLE_ENTITY.*")

import gradio as gr

import core
from style import CSS, HEAD

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
    history = history + [{"role": "assistant", "content": THINKING}]
    yield history, session_id

    reply, sid = "", session_id
    async for reply, sid in core.stream_reply(user_msg, session_id):
        history[-1]["content"] = reply
        yield history, sid

    history[-1]["content"] = reply or "I couldn't find relevant information. Could you rephrase your question?"
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


def launch(**kwargs):
    """Build and launch the app."""
    return build_demo().launch(css=CSS, head=HEAD, theme=gr.themes.Base(), **kwargs)


if __name__ == "__main__":
    launch()
