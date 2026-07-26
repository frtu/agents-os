"""Request bodies for decision endpoints. Response shapes reuse the domain
models directly (already camelCase). Fields are optional so a missing body is
tolerated, matching the frontend which omits bodies for approve/continue/etc."""
from __future__ import annotations

from app.domain.models import Schema


class RejectBody(Schema):
    comment: str | None = None


class ClarifyBody(Schema):
    message: str | None = None


class SelectBody(Schema):
    option_id: str | None = None
