"""Durable conversation store (spec 002 T015/T016; FR-3, FR-7, FR-13; spec 012).

One Markdown file per conversation at
``<workspace>/sessions/YYYY-MM-DD-HH-MM-SS-<conversation-id>-<slug>.md`` (spec 012 FR-1). The file *is* the
source of truth (Constitution P1): a conversation is resumable by id even after a service restart,
since context is reconstructed from disk, not memory.

Two properties distinguish this store from a plain "write the file when you get an id":

* **Lazy creation** (spec 012 FR-2). A ``Conversation`` with ``path is None`` does not exist on
  disk. Only ``append_turn``, ``append_event`` and ``_rewrite_frontmatter`` materialize it, so a
  status probe, a listing, or a pending-plan lookup leaves no empty record behind.
* **The header is rendered from a template** (spec 012 FR-3). ``templates/template-conversation.md``
  is human-owned (Constitution P7): it owns the frontmatter keys, their order and their
  capitalization. Code substitutes placeholders and drops any line whose value is empty.

Layout::

    ---
    Category: session
    Id: <id>
    Created: YYYY-MM-DDTHH:MM:SS
    Tags: [a, b]
    Sdk-session-id: <disposable cache, optional>
    Pending-plan: {json}          # present only while a plan awaits approval
    Pending-interaction: {json}   # present only while a card awaits an answer
    ---

    # Conversation — <name>

    ## [YYYY-MM-DD HH:MM] user
    <message>

    ## [YYYY-MM-DD HH:MM] assistant
    <reply>

Turn blocks are strictly append-only (never rewritten). The name lives in the H1 — in the body,
which frontmatter rewrites never touch — so it cannot be clobbered mid-conversation, and the
filename slug is *derived* from it (spec 012 FR-6: never renamed). The filename's timestamp prefix
is likewise derived from ``Created`` (spec 012 FR-12), so name and record cannot disagree about when
the conversation started.
"""

from __future__ import annotations

import json
import re
import unicodedata
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from functools import lru_cache
from pathlib import Path

from . import vault as vault_mod

# The repo root holds templates/ (this package lives at <root>/app) — same resolution as persona.py.
_ROOT = Path(__file__).resolve().parent.parent
_TEMPLATE = _ROOT / "templates" / "template-conversation.md"

# Used only when the human-owned template is missing or unreadable: a deleted template must degrade
# the header, not break chat (spec 012 D1).
_TEMPLATE_FALLBACK = """\
---
Category: session
Id: {{conversation-id}}
Created: {{created}}
Tags: [{{tag-list}}]
Sdk-session-id: {{sdk-session-id}}
Pending-plan: {{plan}}
Pending-interaction: {{interaction}}
---

# Conversation — {{conversation-name}}

{{logs}}
"""

_NAME_HEADING = re.compile(r"^#\s+Conversation\s+—\s*(.+)$", re.MULTILINE)
# spec 012 FR-13: the `{{#event-message}}…{{/event-message}}` loop body — one message block per
# iteration. Extracted from the human-owned template so its shape governs the log body, not just the
# header (Constitution P7).
_EVENT_SECTION = re.compile(
    r"\{\{#event-message\}\}\n?(.*?)\n?\{\{/event-message\}\}", re.DOTALL
)
# Used when the template is missing/unreadable or carries no event-message section: the message body
# must degrade to a readable block, not break chat (mirrors _TEMPLATE_FALLBACK, spec 012 D1).
_EVENT_SECTION_FALLBACK = "## {{role}} - {{event-time}}\n{{message}}"
# spec 012 FR-14: the FR-13 header `## <role> - <event-time>`. The timestamp shape is pinned so a
# message body that happens to start with `## word - text` is not mistaken for a turn header.
_NEW_HEADER = re.compile(
    r"^##\s+(?P<role>\S+)\s+-\s+(?P<ts>\d{4}-\d{2}-\d{2} \d{2}:\d{2})\s*$"
)
# The id inside a dated filename, with the time part optional so a pre-FR-12 name still reads.
_FILENAME_ID = re.compile(r"^\d{4}-\d{2}-\d{2}(?:-\d{2}-\d{2}-\d{2})?-([^-]+)-")
_PLACEHOLDER = re.compile(r"\{\{[^}]*\}\}")
# A frontmatter line left with a key and nothing after it — i.e. a field this conversation has no
# value for. `Tags: []` is deliberately *not* matched: an empty list is a value.
_EMPTY_FIELD = re.compile(r"^[A-Za-z][A-Za-z0-9-]*:\s*$")

# A name that slugifies to nothing (emoji, punctuation, non-Latin scripts) still needs a filename.
_UNNAMED = "conversation"


@dataclass
class Turn:
    role: str
    timestamp: str
    text: str


@dataclass
class Conversation:
    conversation_id: str
    workspace: Path
    created: str
    # `None` *is* "not on disk yet" (spec 012 FR-2/D3) — one nullable field rather than a separate
    # flag that could disagree with it, and every unguarded use becomes a type error.
    path: Path | None = None
    name: str = ""
    tags: list[str] = field(default_factory=list)
    sdk_session_id: str | None = None
    pending_plan: dict | None = None  # {"request": str, "plan": {...models.Plan...}}
    # spec 008 FR-11: a durable, blocking agent→user interaction awaiting a response.
    # Shape: a serialised models.Interaction dict, optionally carrying a "plan"/"request"
    # payload when the interaction wraps a plan-first approval (FR-17).
    pending_interaction: dict | None = None
    turns: list[Turn] = field(default_factory=list)


def new_id() -> str:
    return uuid.uuid4().hex[:12]


def now_created() -> str:
    """A `Created` value: ISO-8601 local time, second precision (spec 012 FR-12)."""
    return datetime.now().isoformat(timespec="seconds")


def filename_stamp(created: str) -> str:
    """The FR-1 filename prefix for a `Created` value: ISO with `T` and `:` turned into hyphens.

    A `:` is not portable in a filename, and the frontmatter already carries the exact ISO form for
    machines (spec 012 D7). A date-only `Created` — hand-written, or pre-FR-12 — keeps its shape
    rather than gaining a fabricated midnight.
    """
    return created.replace("T", "-").replace(":", "-")


def materialized(conv: Conversation) -> bool:
    """Whether this conversation has a file on disk yet (spec 012 FR-2)."""
    return conv.path is not None


# --- naming ----------------------------------------------------------------


def slugify(text: str, *, cap: int = 48) -> str:
    """A filename-safe slug of `text`, or `conversation` when nothing survives (spec 012 FR-1/FR-5).

    Reducing to ``[a-z0-9-]`` also means a name can never carry a path separator or ``..`` into
    ``_target_path``. That is belt; ``vault.guard_write_path`` in ``_ensure_materialized`` is braces.
    """
    decomposed = unicodedata.normalize("NFKD", text)
    stripped = "".join(ch for ch in decomposed if unicodedata.category(ch) != "Mn")
    slug = re.sub(r"[^a-z0-9]+", "-", stripped.lower()).strip("-")
    if len(slug) > cap:
        slug = slug[:cap]
        # Cut back to a word boundary so the name does not end mid-word, unless that would leave
        # almost nothing.
        head, _, _tail = slug.rpartition("-")
        if len(head) >= cap // 3:
            slug = head
        slug = slug.strip("-")
    return slug or _UNNAMED


def fallback_name(message: str) -> str:
    """A deterministic name from the user's first message (spec 012 FR-5)."""
    first = next((line.strip() for line in message.splitlines() if line.strip()), "")
    if not first:
        return _UNNAMED
    if len(first) > 60:
        first = first[:60]
        head, _, _tail = first.rpartition(" ")
        first = head or first
    return first or _UNNAMED


def set_name(conv: Conversation, name: str, tags: list[str] | None = None) -> None:
    """Name an unmaterialized conversation; a no-op once the file exists (spec 012 FR-6).

    This is the *entire* enforcement of "never renamed": there is no code path that changes the name
    of a record that already has a path, so no code path can move its file.
    """
    if conv.path is not None:
        return
    cleaned = name.strip()
    if cleaned:
        conv.name = cleaned
    if tags is not None:
        conv.tags = [t for t in (t.strip() for t in tags) if t]


# --- template rendering (spec 012 FR-3) ------------------------------------


@lru_cache(maxsize=1)
def _template_text() -> str:
    try:
        return _TEMPLATE.read_text(encoding="utf-8")
    except OSError:
        return _TEMPLATE_FALLBACK


def _template_parts() -> tuple[list[str], list[str]]:
    """The template split into (frontmatter lines, body lines) — the `{{logs}}` line is dropped."""
    text = _template_text()
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return [], [ln for ln in lines if "{{logs}}" not in ln]
    try:
        close = lines.index("---", 1)
    except ValueError:
        return [], [ln for ln in lines if "{{logs}}" not in ln]
    front = lines[1:close]
    body = [ln for ln in lines[close + 1:] if "{{logs}}" not in ln]
    while body and not body[0].strip():
        body.pop(0)
    while body and not body[-1].strip():
        body.pop()
    return front, body


def _substitutions(conv: Conversation) -> dict[str, str]:
    return {
        "{{conversation-id}}": conv.conversation_id,
        "{{created}}": conv.created,
        "{{tag-list}}": ", ".join(conv.tags),
        "{{conversation-name}}": conv.name,
        "{{sdk-session-id}}": conv.sdk_session_id or "",
        "{{plan}}": json.dumps(conv.pending_plan, ensure_ascii=False) if conv.pending_plan else "",
        "{{interaction}}": (
            json.dumps(conv.pending_interaction, ensure_ascii=False)
            if conv.pending_interaction
            else ""
        ),
    }


def _render_lines(lines: list[str], conv: Conversation) -> list[str]:
    """Substitute placeholders, dropping any line left without a value (spec 012 FR-3).

    One rule reconciles a static template with the app's conditional fields: `Pending-plan` is a
    line in the template but only sometimes a line in the file. Dropping a line whose placeholder
    resolved to nothing means a human can add or remove a field without touching code.
    """
    subs = _substitutions(conv)
    out: list[str] = []
    for line in lines:
        rendered = line
        for token, value in subs.items():
            rendered = rendered.replace(token, value)
        if _PLACEHOLDER.search(rendered):  # a placeholder this build does not know
            continue
        if _EMPTY_FIELD.match(rendered):
            continue
        out.append(rendered)
    return out


def _render_frontmatter(conv: Conversation) -> str:
    front, _ = _template_parts()
    lines = ["---", *_render_lines(front, conv), "---"]
    return "\n".join(lines) + "\n"


def _render_header(conv: Conversation) -> str:
    """Frontmatter + the name heading — written once, at materialization (spec 012 FR-3/D2).

    The event-message loop is part of the template body but is not a header line, so it is dropped
    here (like `{{logs}}`): the header is rendered once, message blocks are appended per turn by
    ``render_message_block`` (spec 012 FR-13).
    """
    _, body = _template_parts()
    rendered_body = _render_lines(body, conv)
    text = _render_frontmatter(conv)
    if rendered_body:
        text += "\n" + "\n".join(rendered_body) + "\n"
    return text


@lru_cache(maxsize=1)
def _event_section() -> str:
    """The `{{#event-message}}` loop body from the template (spec 012 FR-13), or a fallback block."""
    m = _EVENT_SECTION.search(_template_text())
    return m.group(1) if m else _EVENT_SECTION_FALLBACK


def render_message_block(role: str, event_time: str, message: str) -> str:
    """Render one message block through the template's event-message loop (spec 012 FR-13).

    One iteration of the mustache loop: substitute `{{role}}`, `{{event-time}}`, `{{message}}` into
    the human-owned section, yielding a `## <role> - <event-time>` block followed by the body.
    """
    subs = {"{{role}}": role, "{{event-time}}": event_time, "{{message}}": message.strip()}
    out = _event_section()
    for token, value in subs.items():
        out = out.replace(token, value)
    return out


# --- (de)serialisation -----------------------------------------------------


def _parse(text: str) -> tuple[dict, str]:
    """Split a session file into (frontmatter dict, body markdown).

    Keys are lowercased (spec 012 FR-8) so the template's `Id:`/`Created:` and the legacy
    `conversation-id:`/`created:` both read the same, which is what makes pre-012 files load
    without a migration step.
    """
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
        front[key.strip().lower()] = value.strip()
    return front, body


def _parse_name(body: str) -> str:
    m = _NAME_HEADING.search(body)
    return m.group(1).strip() if m else ""


def _parse_tags(raw: str) -> list[str]:
    return [t for t in (part.strip() for part in raw.strip("[]").split(",")) if t]


def _parse_turns(body: str) -> list[Turn]:
    turns: list[Turn] = []
    role: str | None = None
    ts = ""
    buf: list[str] = []

    def flush() -> None:
        if role is not None:
            turns.append(Turn(role=role, timestamp=ts, text="\n".join(buf).strip()))

    for line in body.splitlines():
        new = _NEW_HEADER.match(line)  # spec 012 FR-14: `## <role> - <time>`
        if line.startswith("## [") and "] " in line:  # legacy `## [<time>] <role>`
            flush()
            header = line[4:]
            ts, _, role = header.partition("] ")
            role = role.strip()
            buf = []
        elif new:
            flush()
            role = new.group("role").strip()
            ts = new.group("ts").strip()
            buf = []
        else:
            buf.append(line)
    flush()
    return turns


# --- store API -------------------------------------------------------------


def _sessions_dir(workspace: Path) -> Path:
    return workspace / "sessions"


def _file_id(path: Path) -> str:
    """The id segment of a dated filename, or the whole stem for a pre-012 flat file.

    Matched rather than counted to: the prefix carries a time now and did not before (spec 012
    FR-7/D7), so both `YYYY-MM-DD-HH-MM-SS-<id>-<slug>` and `YYYY-MM-DD-<id>-<slug>` must read.
    """
    m = _FILENAME_ID.match(path.stem)
    return m.group(1) if m else path.stem


def path_for(workspace: Path, conversation_id: str) -> Path | None:
    """Locate a conversation's file by scanning `sessions/` (spec 012 FR-7).

    The id is in the filename, so this is an exact glob rather than a parse of every file. Several
    matches must not raise — a chat turn dying on a duplicate would be worse than picking one — so
    the `Id:` field breaks the tie and mtime breaks that.
    """
    sessions = _sessions_dir(workspace)
    if not sessions.is_dir():
        return None
    matches = sorted(sessions.glob(f"*-{conversation_id}-*.md"))
    if len(matches) == 1:
        return matches[0]
    if matches:
        verified = []
        for p in matches:
            front, _ = _parse(p.read_text(encoding="utf-8"))
            if conversation_id in (front.get("id"), front.get("conversation-id")):
                verified.append(p)
        return max(verified or matches, key=lambda p: p.stat().st_mtime)
    legacy = sessions / f"{conversation_id}.md"  # pre-012 flat name (FR-7, D6)
    return legacy if legacy.is_file() else None


def load_path(workspace: Path, path: Path) -> Conversation | None:
    """Parse one session file, or `None` if it is not a conversation (spec 012 FR-9).

    The listing hands us whatever `*.md` happens to sit in `sessions/`, and a human may well drop a
    note there. A record is recognisable by carrying an id or at least one turn block; without
    either there is nothing to resume, so it is skipped rather than listed as an empty conversation.
    """
    if not path.is_file():
        return None
    front, body = _parse(path.read_text(encoding="utf-8"))
    front_id = front.get("id") or front.get("conversation-id")
    turns = _parse_turns(body)
    if not front_id and not turns:
        return None
    pending = front.get("pending-plan")
    pending_itx = front.get("pending-interaction")
    return Conversation(
        conversation_id=front_id or _file_id(path),
        path=path,
        workspace=workspace,
        created=front.get("created") or now_created(),
        name=_parse_name(body),
        tags=_parse_tags(front.get("tags", "")),
        sdk_session_id=front.get("sdk-session-id") or None,
        pending_plan=json.loads(pending) if pending else None,
        pending_interaction=json.loads(pending_itx) if pending_itx else None,
        turns=turns,
    )


def load(workspace: Path, conversation_id: str) -> Conversation | None:
    p = path_for(workspace, conversation_id)
    return load_path(workspace, p) if p is not None else None


def load_or_new(workspace: Path, conversation_id: str | None) -> Conversation:
    """Load an existing conversation, or build an unsaved one — touches no disk (spec 012 FR-2)."""
    if conversation_id:
        existing = load(workspace, conversation_id)
        if existing is not None:
            return existing
    return Conversation(
        conversation_id=conversation_id or new_id(),
        workspace=workspace,
        created=now_created(),
    )


def _target_path(conv: Conversation) -> Path:
    slug = slugify(conv.name) if conv.name else _UNNAMED
    stamp = filename_stamp(conv.created)
    return _sessions_dir(conv.workspace) / f"{stamp}-{conv.conversation_id}-{slug}.md"


def _ensure_materialized(conv: Conversation) -> Path:
    """Create the file on first durable write (spec 012 FR-1/FR-2), fixing its name for good.

    Adopting an already-existing file for this id matters: two in-memory ``Conversation`` objects can
    describe the same thread (a chat turn holds one while the concierge loads another to persist a
    pause), and only one file may exist per id. Whoever writes first names it (FR-6).
    """
    if conv.path is not None:
        return conv.path
    existing = path_for(conv.workspace, conv.conversation_id)
    if existing is not None:
        conv.path = existing
        return existing
    if not conv.name:
        conv.name = _UNNAMED
    target = _target_path(conv)
    target.parent.mkdir(parents=True, exist_ok=True)
    vault_mod.guard_write_path(conv.workspace, target)
    target.write_text(_render_header(conv), encoding="utf-8")
    conv.path = target
    return target


def append_message_block(conv: Conversation, role: str, event_time: str, text: str) -> None:
    """Append one message block via the template's event-message loop (spec 012 FR-13, FR-7).

    The single message-writing primitive: `append_turn`, `append_event` and the `conversation-view`
    entity all go through here, so the on-disk format has one source of truth. Strictly append-only
    (never rewrites a prior block) and always through the `vault/raw/` guard (P2).
    """
    path = _ensure_materialized(conv)
    vault_mod.guard_write_path(conv.workspace, path)
    block = "\n" + render_message_block(role, event_time, text) + "\n"
    with path.open("a", encoding="utf-8") as fh:
        fh.write(block)
    conv.turns.append(Turn(role, event_time, text.strip()))


def append_turn(conv: Conversation, user_message: str, assistant_reply: str) -> None:
    """Append one user+assistant turn — never rewrites prior lines (FR-7, spec 012 FR-13)."""
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    append_message_block(conv, "user", stamp, user_message)
    append_message_block(conv, "assistant", stamp, assistant_reply)


def append_event(conv: Conversation, label: str, text: str) -> None:
    """Append a single labelled block (append-only) — used to capture interactions (spec 008 FR-13).

    Unlike ``append_turn`` (a user+assistant pair) this records one event, e.g. an interaction
    request or its resolution, so decisions stay auditable in the durable ``sessions/`` record.
    """
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    append_message_block(conv, label, stamp, text)


def _maybe_json(raw: str):
    return json.loads(raw) if raw else None


# The frontmatter fields that change over a thread's life, and how to read one back off disk. Name,
# tags, id and created date are fixed at materialization (FR-6), so only these three can be clobbered.
_MUTABLE_FIELDS = {
    "sdk_session_id": ("sdk-session-id", lambda raw: raw or None),
    "pending_plan": ("pending-plan", _maybe_json),
    "pending_interaction": ("pending-interaction", _maybe_json),
}


def _set_front_field(conv: Conversation, attr: str, value) -> None:
    """Persist one durable frontmatter field, leaving the others as they are **on disk**.

    Two in-memory `Conversation` objects routinely describe one thread: a chat turn holds one loaded
    before the stream, while `capabilities.create_interaction` loads another mid-stream to persist a
    card. Rendering the whole frontmatter block from a single instance let it erase fields it had
    never seen — an agent-raised clarification was written, then wiped by the same turn's
    `set_sdk_session_id`, so the card on screen had no durable record behind it and answering it was
    rejected as "no longer awaiting a response" (spec 008 FR-11).

    Re-reading also refreshes `conv`, so the caller's own view stops being stale.
    """
    if attr not in _MUTABLE_FIELDS:
        raise KeyError(f"not a durable frontmatter field: {attr!r}")
    path = _ensure_materialized(conv)
    vault_mod.guard_write_path(conv.workspace, path)
    front, body = _parse(path.read_text(encoding="utf-8"))
    for other, (key, read) in _MUTABLE_FIELDS.items():
        setattr(conv, other, value if other == attr else read(front.get(key, "")))
    path.write_text(_render_frontmatter(conv) + body, encoding="utf-8")


def set_pending_plan(conv: Conversation, request: str, plan: dict) -> None:
    _set_front_field(conv, "pending_plan", {"request": request, "plan": plan})


def clear_pending_plan(conv: Conversation) -> None:
    _set_front_field(conv, "pending_plan", None)


def set_pending_interaction(conv: Conversation, interaction: dict) -> None:
    """Persist a blocking interaction as the durable source of truth (spec 008 FR-11, P1)."""
    _set_front_field(conv, "pending_interaction", interaction)


def clear_pending_interaction(conv: Conversation) -> None:
    _set_front_field(conv, "pending_interaction", None)


def set_sdk_session_id(conv: Conversation, sdk_session_id: str | None) -> None:
    if sdk_session_id and sdk_session_id != conv.sdk_session_id:
        _set_front_field(conv, "sdk_session_id", sdk_session_id)


def replay_history(conv: Conversation, max_turns: int = 12) -> str:
    """Render recent turns as plain text to prime a resumed agent (FR-3/FR-13)."""
    recent = conv.turns[-max_turns * 2:]
    return "\n".join(f"{t.role}: {t.text}" for t in recent)
