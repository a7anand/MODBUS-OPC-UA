# Copyright (c) 2026 Aman Anand, M (T&I), Barauni
"""Audit trail (in-memory; SQLite in later persistence)."""

from __future__ import annotations

import threading
from collections import deque
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    pass


@dataclass
class AuditRecord:
    timestamp: datetime
    username: str
    action: str
    object_name: str
    old_value: str
    new_value: str
    source: str
    result: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "timestamp": self.timestamp.isoformat(),
            "username": self.username,
            "action": self.action,
            "object": self.object_name,
            "old_value": self.old_value,
            "new_value": self.new_value,
            "source": self.source,
            "result": self.result,
        }


class AuditManager:
    def __init__(self, capacity: int = 5000) -> None:
        self._lock = threading.RLock()
        self._records: deque[AuditRecord] = deque(maxlen=capacity)
        self._store: Any = None

    def set_store(self, store: Any) -> None:
        self._store = store

    def record(
        self,
        username: str,
        action: str,
        object_name: str,
        old_value: str = "",
        new_value: str = "",
        source: str = "api",
        result: str = "OK",
    ) -> None:
        rec = AuditRecord(
            timestamp=datetime.now(timezone.utc),
            username=username,
            action=action,
            object_name=object_name,
            old_value=old_value,
            new_value=new_value,
            source=source,
            result=result,
        )
        with self._lock:
            self._records.appendleft(rec)
        if self._store is not None:
            self._store.insert_audit(
                username, action, object_name, old_value, new_value, source, result
            )

    def list_records(self, limit: int = 200) -> list[dict[str, Any]]:
        with self._lock:
            return [r.to_dict() for r in list(self._records)[:limit]]
