"""Application errors, mapped to problem+json by app/api/errors.py."""
from __future__ import annotations


class NotFoundError(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class InvariantError(Exception):
    """A command that violates an aggregate invariant (maps to HTTP 422)."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class ConflictError(Exception):
    """A command blocked by the current state of related data (maps to HTTP 409),
    e.g. deleting a workflow definition still referenced by a planning object."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message
