# Copyright (c) 2026 Aman Anand, M (T&I), Barauni
"""Operational events."""

from __future__ import annotations

import threading
from collections import deque
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from app.core.persistence import SqliteStore


class EventSeverity(str, Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


@dataclass
class GatewayEvent:
    timestamp: datetime
    severity: EventSeverity
    message: str
    source: str = "gateway"
    details: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "timestamp": self.timestamp.isoformat(),
            "severity": self.severity.value,
            "message": self.message,
            "source": self.source,
            "details": self.details or {},
        }


class EventManager:
    def __init__(self, capacity: int = 5000) -> None:
        self._lock = threading.RLock()
        self._events: deque[GatewayEvent] = deque(maxlen=capacity)
        self._store: Any = None

    def set_store(self, store: Any) -> None:
        self._store = store

    def emit(
        self,
        message: str,
        severity: EventSeverity = EventSeverity.INFO,
        source: str = "gateway",
        **details: Any,
    ) -> None:
        ev = GatewayEvent(
            timestamp=datetime.now(timezone.utc),
            severity=severity,
            message=message,
            source=source,
            details=details or None,
        )
        with self._lock:
            self._events.appendleft(ev)
        if self._store is not None:
            self._store.insert_event(severity.value, message, source, details or {})

    def list_events(self, limit: int = 200) -> list[dict[str, Any]]:
        with self._lock:
            return [e.to_dict() for e in list(self._events)[:limit]]
