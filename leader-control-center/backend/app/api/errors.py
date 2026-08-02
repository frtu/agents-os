"""Problem+JSON error handling (specs/api/rest-api.md §Errors)."""
from __future__ import annotations

from fastapi import Request
from fastapi.responses import JSONResponse

from app.application.service import ConflictError, InvariantError, NotFoundError

_MEDIA = "application/problem+json"


def _problem(status: int, title: str, detail: str, instance: str) -> JSONResponse:
    return JSONResponse(
        status_code=status,
        media_type=_MEDIA,
        content={
            "type": "about:blank",
            "title": title,
            "status": status,
            "detail": detail,
            "instance": instance,
        },
    )


async def not_found_handler(request: Request, exc: NotFoundError) -> JSONResponse:
    return _problem(404, "Not Found", exc.message, str(request.url.path))


async def invariant_handler(request: Request, exc: InvariantError) -> JSONResponse:
    return _problem(422, "Unprocessable Entity", exc.message, str(request.url.path))


async def conflict_handler(request: Request, exc: ConflictError) -> JSONResponse:
    return _problem(409, "Conflict", exc.message, str(request.url.path))


def register_error_handlers(app) -> None:
    app.add_exception_handler(NotFoundError, not_found_handler)
    app.add_exception_handler(InvariantError, invariant_handler)
    app.add_exception_handler(ConflictError, conflict_handler)
