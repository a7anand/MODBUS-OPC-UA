# Copyright (c) 2026 Aman Anand, M (T&I), Barauni
"""HTTP health and status API."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING

from fastapi import FastAPI
from pydantic import BaseModel

from gateway import __author__, __version__

if TYPE_CHECKING:
    from gateway.poller import Poller


class HealthResponse(BaseModel):
    status: str
    version: str
    author: str
    timestamp: str


def create_app(poller: Poller | None = None) -> FastAPI:
    app = FastAPI(
        title="AA Modbus OPC UA Gateway",
        description="Health and diagnostics",
        version=__version__,
    )

    @app.get("/health", response_model=HealthResponse)
    async def health() -> HealthResponse:
        return HealthResponse(
            status="ok",
            version=__version__,
            author=__author__,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

    @app.get("/status")
    async def status():
        if poller is None:
            return {"poll_groups": {}}
        return {
            "poll_groups": {
                gid: {
                    "polls": s.polls,
                    "errors": s.errors,
                    "last_poll_at": s.last_poll_at.isoformat() if s.last_poll_at else None,
                    "last_error": s.last_error,
                }
                for gid, s in poller.stats.items()
            }
        }

    return app
