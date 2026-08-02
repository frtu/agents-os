"""FastAPI application factory. Boots the control center (restoring state from
SQLite or seeding on first run), mounts the REST + WebSocket API under /api/v1,
and runs the simulation engine on a background tick so executions advance, raise
Human Requests, and produce Artifacts without any external engine (Temporal slots
in behind the same port later)."""
from __future__ import annotations

import asyncio
import contextlib
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import ws
from app.api.errors import register_error_handlers
from app.api.routers import (
    artifacts,
    attention,
    boards,
    catalog,
    executions,
    notifications,
    stories,
    tasks,
    workflows,
)
from app.application.service import build_control_center
from app.config import settings

_API_PREFIX = "/api/v1"

# Log under uvicorn's own logger so our lines share its formatting and level.
log = logging.getLogger("uvicorn.error")


async def _simulation_loop(app: FastAPI) -> None:
    interval = settings.simulation_tick_seconds
    while True:
        await asyncio.sleep(interval)
        # A single bad tick must not silently kill the background task — log it
        # and keep ticking so the engine recovers on the next iteration.
        try:
            app.state.control_center.engine.tick()
        except Exception:
            log.exception("Simulation tick failed; continuing")


@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info(
        "Starting Leader Control Center (tick=%.1fs, cors=%s)",
        settings.simulation_tick_seconds,
        ", ".join(settings.cors_origins) or "(none)",
    )
    app.state.control_center = build_control_center()
    tick_task: asyncio.Task | None = None
    if settings.simulation_tick_seconds > 0:
        tick_task = asyncio.create_task(_simulation_loop(app))
        log.info("Simulation engine ticking every %.1fs", settings.simulation_tick_seconds)
    else:
        log.info("Simulation engine disabled (SIMULATION_TICK_SECONDS<=0)")
    try:
        yield
    finally:
        log.info("Shutting down — cancelling tick loop and closing SQLite")
        if tick_task is not None:
            tick_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await tick_task
        db = app.state.control_center.store.db
        if db is not None:
            db.close()


def create_app() -> FastAPI:
    app = FastAPI(title="Leader Control Center", version="0.1.0", lifespan=lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    register_error_handlers(app)

    for router in (
        boards.router,
        stories.router,
        tasks.router,
        executions.router,
        artifacts.router,
        attention.router,
        catalog.router,
        notifications.router,
        workflows.router,
        ws.router,
    ):
        app.include_router(router, prefix=_API_PREFIX)

    return app


app = create_app()
