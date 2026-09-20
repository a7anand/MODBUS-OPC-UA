# Copyright (c) 2026 Aman Anand, M (T&I), Barauni
"""Gateway health metrics."""

from __future__ import annotations

import os
import time
from typing import Any


class HealthMonitor:
    def __init__(self) -> None:
        self._started = time.time()

    def snapshot(self, extra: dict[str, Any] | None = None) -> dict[str, Any]:
        data = {
            "uptime_sec": round(time.time() - self._started, 1),
            "pid": os.getpid(),
            "status": "running",
        }
        if extra:
            data.update(extra)
        return data
