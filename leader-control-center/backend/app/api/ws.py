"""WebSocket transport (specs/api/realtime.md). One connection per session; the
server broadcasts every realtime message (the client uses them to invalidate
cached queries, so per-topic filtering is not required for the MVP). Subscribe/
unsubscribe frames are accepted and ignored."""
from __future__ import annotations

import asyncio

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.domain.events import RealtimeMessage

router = APIRouter()


async def _send_loop(websocket: WebSocket, queue: "asyncio.Queue[RealtimeMessage]") -> None:
    while True:
        msg = await queue.get()
        await websocket.send_text(msg.model_dump_json(by_alias=True))


async def _recv_loop(websocket: WebSocket) -> None:
    # Drain client frames (subscribe/unsubscribe). Broadcast model ignores them.
    while True:
        await websocket.receive_text()


@router.websocket("/stream")
async def stream(websocket: WebSocket) -> None:
    await websocket.accept()
    control_center = websocket.app.state.control_center
    bus = control_center.store.bus

    queue: "asyncio.Queue[RealtimeMessage]" = asyncio.Queue()
    unsubscribe = bus.subscribe(queue.put_nowait)

    sender = asyncio.create_task(_send_loop(websocket, queue))
    receiver = asyncio.create_task(_recv_loop(websocket))
    try:
        await asyncio.wait({sender, receiver}, return_when=asyncio.FIRST_COMPLETED)
    except WebSocketDisconnect:
        pass
    finally:
        unsubscribe()
        for task in (sender, receiver):
            task.cancel()
