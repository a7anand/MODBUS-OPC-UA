# Copyright (c) 2026 Aman Anand, M (T&I), Barauni
"""Modbus diagnostic read/write and communication monitor buffer."""

from __future__ import annotations

import threading
from collections import deque
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from app.core.enums import RegisterArea
from app.modbus.base import ModbusEngine
from app.modbus.register_codec import diagnostic_interpretations


@dataclass
class CommRecord:
    timestamp: datetime
    protocol: str
    device: str
    direction: str
    operation: str
    address: Any
    value: Any
    result: str
    response_time_ms: float
    error: str | None
    tag_name: str = ""
    tx_hex: str = ""
    rx_hex: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "timestamp": self.timestamp.isoformat(),
            "protocol": self.protocol,
            "device": self.device,
            "tag_name": self.tag_name,
            "direction": self.direction,
            "operation": self.operation,
            "address": self.address,
            "value": self.value,
            "result": self.result,
            "response_time_ms": self.response_time_ms,
            "error": self.error,
            "tx_hex": self.tx_hex,
            "rx_hex": self.rx_hex,
        }


class CommunicationMonitor:
    def __init__(self, capacity: int = 10000) -> None:
        self._lock = threading.RLock()
        self._records: deque[CommRecord] = deque(maxlen=capacity)
        self._paused = False

    def pause(self) -> None:
        self._paused = True

    def resume(self) -> None:
        self._paused = False

    def clear(self) -> None:
        with self._lock:
            self._records.clear()

    def log(
        self,
        protocol: str,
        device: str,
        direction: str,
        operation: str = "read",
        address: Any = None,
        value: Any = None,
        ok: bool = True,
        response_ms: float = 0.0,
        error: str | None = None,
        tag_name: str = "",
        tx_hex: str = "",
        rx_hex: str = "",
    ) -> None:
        if self._paused:
            return
        rec = CommRecord(
            timestamp=datetime.now(timezone.utc),
            protocol=protocol,
            device=device,
            direction=direction,
            operation=operation,
            address=address,
            value=value,
            result="OK" if ok else "FAIL",
            response_time_ms=response_ms,
            error=error,
            tag_name=tag_name,
            tx_hex=tx_hex,
            rx_hex=rx_hex,
        )
        with self._lock:
            self._records.appendleft(rec)

    def export(self, limit: int = 500) -> list[dict[str, Any]]:
        with self._lock:
            return [r.to_dict() for r in list(self._records)[:limit]]


class ModbusDiagnostics:
    def __init__(self, engine: ModbusEngine, monitor: CommunicationMonitor) -> None:
        self._engine = engine
        self._monitor = monitor

    async def read(
        self,
        device: str,
        unit_id: int,
        area: RegisterArea,
        address: int,
        count: int,
    ) -> dict[str, Any]:
        dev = self._engine.get(device)
        result = await dev.read(unit_id, area, address, count)
        self._monitor.log(
            "MODBUS",
            device,
            "RX",
            "diagnostic_read",
            address,
            result.registers if result.ok else None,
            result.ok,
            result.response_time_ms,
            result.error,
        )
        payload: dict[str, Any] = {
            "ok": result.ok,
            "registers": result.registers,
            "error": result.error,
            "response_time_ms": result.response_time_ms,
        }
        if result.ok:
            payload["interpretation"] = diagnostic_interpretations(result.registers)
        return payload

    async def write(
        self,
        device: str,
        unit_id: int,
        area: RegisterArea,
        address: int,
        values: list[int],
    ) -> dict[str, Any]:
        dev = self._engine.get(device)
        result = await dev.write(unit_id, area, address, values)
        self._monitor.log(
            "MODBUS",
            device,
            "TX",
            "diagnostic_write",
            address,
            values,
            result.ok,
            0.0,
            result.error,
        )
        return {"ok": result.ok, "error": result.error}
