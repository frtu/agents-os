"""Problem+JSON error handling (specs/api/rest-api.md §Errors)."""
from __future__ import annotations

from fastapi import Request
from fastapi.responses import JSONResponse

from app.application.service import NotFoundError

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


def register_error_handlers(app) -> None:
    app.add_exception_handler(NotFoundError, not_found_handler)
