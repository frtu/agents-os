"""Core assistant logic with Claude Agent SDK for knowledge retrieval.

The assistant uses Read/Glob/Grep tools to search project documentation
and answer questions based on the knowledge found.
"""
import asyncio
import logging
from pathlib import Path

logger = logging.getLogger("leader-assistant.core")

from claude_agent_sdk import (
    query,
    ClaudeAgentOptions,
    SystemMessage,
    StreamEvent,
    ResultMessage,
)

import skill_manager

KNOWLEDGE_BASE = Path.cwd().parent
AGENT_PROMPT_FILE = Path(__file__).parent / "agents" / "assistant.md"
ASSISTANT_DIR = Path(__file__).parent


def _get_skills_context() -> str:
    """Generate context about available and installed skills."""
    lines = ["## Available Skills\n"]

    # List available skills
    if skill_manager.SKILLS_SOURCE.exists():
        for skill_dir in sorted(skill_manager.SKILLS_SOURCE.iterdir()):
            if skill_dir.is_dir() and not skill_dir.name.startswith("."):
                skill_file = skill_dir / "SKILL.md"
                if skill_file.exists():
                    info = skill_manager.parse_skill_frontmatter(skill_dir)
                    desc = info.get("description", "No description")
                    lines.append(f"- **{skill_dir.name}**: {desc}")

    # List installed skills
    installed = []
    if skill_manager.SKILLS_DEST.exists():
        for item in sorted(skill_manager.SKILLS_DEST.iterdir()):
            if not item.name.startswith(".") and (item.is_symlink() or item.is_dir()):
                installed.append(item.name)

    if installed:
        lines.append(f"\n## Installed Skills: {', '.join(installed)}")
    else:
        lines.append("\n## Installed Skills: None")

    return "\n".join(lines)


def _load_prompt() -> str:
    """Load the agent prompt from agent.md with skills context."""
    base_prompt = AGENT_PROMPT_FILE.read_text()
    skills_context = _get_skills_context()
    return f"{base_prompt}\n\n{skills_context}"

assistant_options = ClaudeAgentOptions(
    system_prompt=_load_prompt(),
    model="sonnet",
    effort="medium",
    allowed_tools=["Read", "Glob", "Grep", "Bash"],
    permission_mode="default",
    cwd=str(ASSISTANT_DIR.resolve()),
    setting_sources=[],
)


async def stream_reply(user_msg: str, session_id: str | None = None):
    """Stream the assistant's reply, yielding (accumulated_text, session_id) as it grows."""
    opts = ClaudeAgentOptions(
        system_prompt=_load_prompt(),
        model="sonnet",
        effort="medium",
        allowed_tools=["Read", "Glob", "Grep", "Bash"],
        permission_mode="default",
        cwd=str(ASSISTANT_DIR.resolve()),
        setting_sources=[],
        include_partial_messages=True,
        resume=session_id,
    )

    reply, sid = "", session_id
    async for message in query(prompt=user_msg, options=opts):
        if isinstance(message, SystemMessage) and message.subtype == "init":
            sid = message.data.get("session_id", sid)
            logger.debug(f"[SDK] init session={sid}")
        elif isinstance(message, StreamEvent):
            ev = message.event
            ev_type = ev.get("type", "")
            if ev_type == "content_block_delta" and ev.get("delta", {}).get("type") == "text_delta":
                reply += ev["delta"]["text"]
                yield reply, sid
            elif ev_type == "tool_use":
                logger.debug(f"[SDK] tool_use: {ev.get('name', 'unknown')}")
            elif ev_type not in ("content_block_delta", "content_block_start", "content_block_stop"):
                logger.debug(f"[SDK] event: {ev_type}")
        elif isinstance(message, ResultMessage):
            sid = message.session_id or sid
            logger.debug(f"[SDK] result session={sid}")
    yield reply, sid


async def get_reply(user_msg: str, session_id: str | None = None) -> tuple[str, str]:
    """Get the full reply without streaming."""
    reply, sid = "", session_id
    async for reply, sid in stream_reply(user_msg, session_id):
        pass
    return reply, sid
