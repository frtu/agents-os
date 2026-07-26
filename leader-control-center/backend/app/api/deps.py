"""FastAPI dependencies: expose the singleton ControlCenter built at startup."""
from __future__ import annotations

from fastapi import Request

from app.application.service import ControlCenter


def get_control_center(request: Request) -> ControlCenter:
    return request.app.state.control_center
