"""Core assistant logic with Claude Agent SDK for knowledge retrieval.

The assistant uses Read/Glob/Grep tools to search project documentation
and answer questions based on the knowledge found.
"""
import asyncio
from pathlib import Path

from claude_agent_sdk import (
    query,
    ClaudeAgentOptions,
    SystemMessage,
    StreamEvent,
    ResultMessage,
)

KNOWLEDGE_BASE = Path.cwd().parent
AGENT_PROMPT_FILE = Path(__file__).parent / "agents" / "assistant.md"


def _load_prompt() -> str:
    """Load the agent prompt from agent.md."""
    return AGENT_PROMPT_FILE.read_text()

assistant_options = ClaudeAgentOptions(
    system_prompt=_load_prompt(),
    model="sonnet",
    effort="medium",
    allowed_tools=["Read", "Glob", "Grep"],
    permission_mode="default",
    cwd=str(KNOWLEDGE_BASE.resolve()),
    setting_sources=[],
)


async def stream_reply(user_msg: str, session_id: str | None = None):
    """Stream the assistant's reply, yielding (accumulated_text, session_id) as it grows."""
    opts = ClaudeAgentOptions(
        system_prompt=_load_prompt(),
        model="sonnet",
        effort="medium",
        allowed_tools=["Read", "Glob", "Grep"],
        permission_mode="default",
        cwd=str(KNOWLEDGE_BASE.resolve()),
        setting_sources=[],
        include_partial_messages=True,
        resume=session_id,
    )

    reply, sid = "", session_id
    async for message in query(prompt=user_msg, options=opts):
        if isinstance(message, SystemMessage) and message.subtype == "init":
            sid = message.data.get("session_id", sid)
        elif isinstance(message, StreamEvent):
            ev = message.event
            if ev.get("type") == "content_block_delta" and ev.get("delta", {}).get("type") == "text_delta":
                reply += ev["delta"]["text"]
                yield reply, sid
        elif isinstance(message, ResultMessage):
            sid = message.session_id or sid
    yield reply, sid


async def get_reply(user_msg: str, session_id: str | None = None) -> tuple[str, str]:
    """Get the full reply without streaming."""
    reply, sid = "", session_id
    async for reply, sid in stream_reply(user_msg, session_id):
        pass
    return reply, sid
