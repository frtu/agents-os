"""Durable conversation store (spec 002 T015/T016; FR-3, FR-7, FR-13).

One Markdown file per conversation at ``<workspace>/sessions/<conversation_id>.md``.
The file *is* the source of truth (Constitution P1): a conversation is resumable
by id even after a service restart, since context is reconstructed from disk, not
memory.

Layout::

    ---
    category: session
    conversation-id: <id>
    created: YYYY-MM-DD
    sdk-session-id: <disposable cache, optional>
    pending-plan: {json}        # present only while a plan awaits approval
    ---
    ## [YYYY-MM-DD HH:MM] user
    <message>

    ## [YYYY-MM-DD HH:MM] assistant
    <reply>

Turn blocks are strictly append-only (never rewritten). The ``pending-plan``
frontmatter line is the single mutable field: set when a consequential plan is
proposed, cleared on approval/execution.
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path

from . import vault as vault_mod

_FRONT_KEYS = ("category", "conversation-id", "created", "sdk-session-id", "pending-plan")


@dataclass
class Turn:
    role: str
    timestamp: str
    text: str


@dataclass
class Conversation:
    conversation_id: str
    path: Path
    workspace: Path
    created: str
    sdk_session_id: str | None = None
    pending_plan: dict | None = None  # {"request": str, "plan": {...models.Plan...}}
    turns: list[Turn] = field(default_factory=list)


def new_id() -> str:
    return uuid.uuid4().hex[:12]


def path_for(workspace: Path, conversation_id: str) -> Path:
    return workspace / "sessions" / f"{conversation_id}.md"


# --- (de)serialisation -----------------------------------------------------


def _render_frontmatter(conv: Conversation) -> str:
    lines = ["---", "category: session", f"conversation-id: {conv.conversation_id}", f"created: {conv.created}"]
    if conv.sdk_session_id:
        lines.append(f"sdk-session-id: {conv.sdk_session_id}")
    if conv.pending_plan is not None:
        lines.append(f"pending-plan: {json.dumps(conv.pending_plan, ensure_ascii=False)}")
    lines.append("---")
    return "\n".join(lines) + "\n"


def _parse(text: str) -> tuple[dict, str]:
    """Split a session file into (frontmatter dict, body markdown)."""
    if not text.startswith("---"):
        return {}, text
    end = text.find("\n---", 3)
    if end == -1:
        return {}, text
    block = text[3:end].strip("\n")
    body = text[end + 4:]
    if body.startswith("\n"):
        body = body[1:]
    front: dict = {}
    for line in block.splitlines():
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        front[key.strip()] = value.strip()
    return front, body


def _parse_turns(body: str) -> list[Turn]:
    turns: list[Turn] = []
    role: str | None = None
    ts = ""
    buf: list[str] = []

    def flush() -> None:
        if role is not None:
            turns.append(Turn(role=role, timestamp=ts, text="\n".join(buf).strip()))

    for line in body.splitlines():
        if line.startswith("## [") and "] " in line:
            flush()
            header = line[4:]
            ts, _, role = header.partition("] ")
            role = role.strip()
            buf = []
        else:
            buf.append(line)
    flush()
    return turns


# --- store API -------------------------------------------------------------


def load(workspace: Path, conversation_id: str) -> Conversation | None:
    p = path_for(workspace, conversation_id)
    if not p.is_file():
        return None
    front, body = _parse(p.read_text(encoding="utf-8"))
    pending = front.get("pending-plan")
    return Conversation(
        conversation_id=front.get("conversation-id", conversation_id),
        path=p,
        workspace=workspace,
        created=front.get("created", date.today().isoformat()),
        sdk_session_id=front.get("sdk-session-id") or None,
        pending_plan=json.loads(pending) if pending else None,
        turns=_parse_turns(body),
    )


def load_or_create(workspace: Path, conversation_id: str | None) -> Conversation:
    if conversation_id:
        existing = load(workspace, conversation_id)
        if existing is not None:
            return existing
    cid = conversation_id or new_id()
    conv = Conversation(
        conversation_id=cid,
        path=path_for(workspace, cid),
        workspace=workspace,
        created=date.today().isoformat(),
    )
    conv.path.parent.mkdir(parents=True, exist_ok=True)
    vault_mod.guard_write_path(workspace, conv.path)
    conv.path.write_text(_render_frontmatter(conv), encoding="utf-8")
    return conv


def append_turn(conv: Conversation, user_message: str, assistant_reply: str) -> None:
    """Append one user+assistant turn — never rewrites prior lines (FR-7)."""
    vault_mod.guard_write_path(conv.workspace, conv.path)
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    block = (
        f"\n## [{stamp}] user\n{user_message.strip()}\n"
        f"\n## [{stamp}] assistant\n{assistant_reply.strip()}\n"
    )
    with conv.path.open("a", encoding="utf-8") as fh:
        fh.write(block)
    conv.turns.append(Turn("user", stamp, user_message.strip()))
    conv.turns.append(Turn("assistant", stamp, assistant_reply.strip()))


def _rewrite_frontmatter(conv: Conversation) -> None:
    """Replace only the frontmatter block; leave turn body bytes untouched."""
    vault_mod.guard_write_path(conv.workspace, conv.path)
    _, body = _parse(conv.path.read_text(encoding="utf-8")) if conv.path.exists() else ({}, "")
    conv.path.write_text(_render_frontmatter(conv) + body, encoding="utf-8")


def set_pending_plan(conv: Conversation, request: str, plan: dict) -> None:
    conv.pending_plan = {"request": request, "plan": plan}
    _rewrite_frontmatter(conv)


def clear_pending_plan(conv: Conversation) -> None:
    conv.pending_plan = None
    _rewrite_frontmatter(conv)


def set_sdk_session_id(conv: Conversation, sdk_session_id: str | None) -> None:
    if sdk_session_id and sdk_session_id != conv.sdk_session_id:
        conv.sdk_session_id = sdk_session_id
        _rewrite_frontmatter(conv)


def replay_history(conv: Conversation, max_turns: int = 12) -> str:
    """Render recent turns as plain text to prime a resumed agent (FR-3/FR-13)."""
    recent = conv.turns[-max_turns * 2:]
    return "\n".join(f"{t.role}: {t.text}" for t in recent)
