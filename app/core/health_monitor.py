# Copyright (c) 2026 Aman Anand, M (T&I), Barauni
"""Gateway health metrics (PDF §32)."""

from __future__ import annotations

import os
import shutil
import time
from typing import Any


class HealthMonitor:
    def __init__(self) -> None:
        self._started = time.time()
        self._last_poll_ms: float = 0.0
        self._poll_error_rate: float = 0.0

    def record_poll_cycle(self, duration_ms: float, errors: int, total: int) -> None:
        self._last_poll_ms = duration_ms
        if total:
            self._poll_error_rate = errors / total

    def snapshot(self, extra: dict[str, Any] | None = None) -> dict[str, Any]:
        data: dict[str, Any] = {
            "uptime_sec": round(time.time() - self._started, 1),
            "pid": os.getpid(),
            "status": "running",
            "last_poll_cycle_ms": round(self._last_poll_ms, 2),
            "poll_error_rate": round(self._poll_error_rate, 4),
        }
        try:
            import psutil

            proc = psutil.Process()
            mem = proc.memory_info()
            data["memory_mb"] = round(mem.rss / (1024 * 1024), 1)
            data["cpu_percent"] = proc.cpu_percent(interval=None)
            du = shutil.disk_usage(os.getcwd())
            data["disk_percent"] = round(du.used / du.total * 100, 1) if du.total else 0
        except Exception:
            data["memory_mb"] = None
            data["cpu_percent"] = None
            data["disk_percent"] = None
        if extra:
            data.update(extra)
        return data
