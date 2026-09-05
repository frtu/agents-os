"""The `conversation-view` entity (spec 002 FR-15/FR-16).

A stateful facade, keyed by a conversation id, that owns a turn's *final* interaction with the user:
it emits each completed message to the surface as an ``event-message`` **and** appends that same
message to the durable conversation log, so the text shown and the text stored come from one place
(FR-15). Centralising both here means no capability appends a message to the log by another path.

It is built over the durable store (:mod:`app.conversation`): id resolution, materialization and
frontmatter persistence stay there; this entity adds the single message-writing path and the
``event-message`` shape the stream carries (FR-16, [[012-conversation-naming]] FR-13).
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from . import conversation as convo
from . import models


def _stamp() -> str:
    """Local time a message was produced (spec 002 FR-16; matches the log's FR-13 event-time)."""
    return datetime.now().strftime("%Y-%m-%d %H:%M")


class ConversationView:
    """Owns final message streaming + log writing for one conversation (spec 002 FR-15)."""

    def __init__(self, conversation: convo.Conversation) -> None:
        self.conversation = conversation

    @classmethod
    def open(cls, workspace: Path, conversation_id: str | None) -> "ConversationView":
        """Load (or build, unsaved) the conversation for an id — touches no disk (spec 012 FR-2)."""
        return cls(convo.load_or_new(workspace, conversation_id))

    @property
    def conversation_id(self) -> str:
        return self.conversation.conversation_id

    def emit(self, role: str, message: str) -> models.EventMessage:
        """Append one completed message to the log and return it as an event-message (FR-15/FR-16)."""
        stamp = _stamp()
        convo.append_message_block(self.conversation, role, stamp, message)
        return models.EventMessage(
            conversation_id=self.conversation.conversation_id,
            role=role,
            event_time=stamp,
            message=message.strip(),
        )

    def emit_turn(self, user_message: str, assistant_reply: str) -> models.EventMessage:
        """Persist a user+assistant pair; return the assistant event-message for the final delta.

        Both blocks share one stamp (a turn happens at one moment), matching the store's
        ``append_turn`` so the on-disk shape is unchanged aside from the FR-13 header format.
        """
        stamp = _stamp()
        convo.append_message_block(self.conversation, "user", stamp, user_message)
        convo.append_message_block(self.conversation, "assistant", stamp, assistant_reply)
        return models.EventMessage(
            conversation_id=self.conversation.conversation_id,
            role="assistant",
            event_time=stamp,
            message=assistant_reply.strip(),
        )

    def record_event(self, label: str, text: str) -> None:
        """Append an audit block (interaction request/resolution/timeout) — same format, no stream."""
        convo.append_message_block(self.conversation, label, _stamp(), text)
