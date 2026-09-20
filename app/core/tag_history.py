# Copyright (c) 2026 Aman Anand, M (T&I), Barauni
"""Rolling tag history for web table (default 5 minutes, in-memory)."""

from __future__ import annotations

import threading
from collections import defaultdict, deque
from datetime import datetime, timedelta, timezone
from typing import Any

from app.core.config_schema import TagDefinition

HISTORY_WINDOW_SEC = 300


def format_registers(registers: list[int], tag: TagDefinition) -> str:
    """Human-readable raw view with byte/word order from tag definition."""
    reg_hex = " ".join(f"{r:04X}" for r in registers)
    return f"{reg_hex} ({tag.byte_order.value}/{tag.word_order.value})"


class TagHistoryBuffer:
    def __init__(self, window_sec: int = HISTORY_WINDOW_SEC) -> None:
        self._window = timedelta(seconds=window_sec)
        self._lock = threading.RLock()
        self._rows: dict[str, deque[dict[str, Any]]] = defaultdict(lambda: deque(maxlen=400))

    def record(
        self,
        tag: TagDefinition,
        value: Any,
        registers: list[int] | None,
    ) -> None:
        now = datetime.now(timezone.utc)
        row = {
            "timestamp": now.isoformat(),
            "device": tag.device,
            "tag": tag.name,
            "value": value,
            "datatype": tag.datatype.value,
            "engineering_unit": tag.engineering_unit,
            "raw": format_registers(registers or [], tag) if registers else "",
        }
        with self._lock:
            self._rows[tag.name].append(row)
            self._prune(tag.name, now)

    def _prune(self, tag_name: str, now: datetime) -> None:
        cutoff = now - self._window
        q = self._rows[tag_name]
        while q and q[0]["timestamp"] < cutoff.isoformat():
            q.popleft()

    def query(
        self,
        device: str | None = None,
        tag: str | None = None,
        limit: int = 500,
    ) -> list[dict[str, Any]]:
        with self._lock:
            names = [tag] if tag else list(self._rows.keys())
            out: list[dict[str, Any]] = []
            for name in names:
                for row in self._rows.get(name, []):
                    if device and row["device"] != device:
                        continue
                    out.append(row)
            out.sort(key=lambda r: r["timestamp"], reverse=True)
            return out[:limit]
