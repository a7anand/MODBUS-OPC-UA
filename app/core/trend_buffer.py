# Copyright (c) 2026 Aman Anand, M (T&I), Barauni
"""In-memory numeric trend samples for web charts (not long-term historian)."""

from __future__ import annotations

import threading
from collections import defaultdict, deque
from datetime import datetime, timezone
from typing import Any


class TrendBuffer:
    def __init__(self, maxlen: int = 300) -> None:
        self._maxlen = maxlen
        self._lock = threading.RLock()
        self._series: dict[str, deque[dict[str, Any]]] = defaultdict(
            lambda: deque(maxlen=self._maxlen)
        )

    def record(self, tag_name: str, value: Any) -> None:
        if isinstance(value, bool):
            numeric = float(int(value))
        elif isinstance(value, (int, float)):
            numeric = float(value)
        else:
            return
        point = {
            "t": datetime.now(timezone.utc).isoformat(),
            "v": numeric,
        }
        with self._lock:
            self._series[tag_name].append(point)

    def series(self, tag_name: str, limit: int = 120) -> list[dict[str, Any]]:
        with self._lock:
            data = list(self._series.get(tag_name, []))
        return data[-limit:]

    def snapshot(self, limit_per_tag: int = 60) -> dict[str, list[dict[str, Any]]]:
        with self._lock:
            return {
                name: list(points)[-limit_per_tag:]
                for name, points in self._series.items()
            }

    def clear(self) -> None:
        with self._lock:
            self._series.clear()
