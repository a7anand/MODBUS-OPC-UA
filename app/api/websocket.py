# Copyright (c) 2026 Aman Anand, M (T&I), Barauni
"""WebSocket real-time updates."""

from __future__ import annotations

import asyncio
import json
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.core.gateway import Gateway

router = APIRouter()


def attach_websocket(app_router: APIRouter, gateway: Gateway) -> None:
    @app_router.websocket("/ws")
    async def ws_endpoint(websocket: WebSocket) -> None:
        await websocket.accept()
        try:
            while True:
                payload: dict[str, Any] = {
                    "tags": gateway.tags.snapshot(),
                    "status": gateway.status(),
                    "events": gateway.events.list_events(20),
                    "communication": gateway.comm_monitor.export(30),
                    "trends": gateway.trends.snapshot(limit_per_tag=40),
                }
                await websocket.send_text(json.dumps(payload))
                await asyncio.sleep(0.75)
        except WebSocketDisconnect:
            return
