# Copyright (c) 2026 Aman Anand, M (T&I), Barauni
"""Modbus device abstraction."""

from __future__ import annotations

import abc
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from app.core.config_schema import ModbusDeviceConfig
from app.core.enums import RegisterArea

logger = logging.getLogger(__name__)


@dataclass
class ReadResult:
    ok: bool
    registers: list[int] = field(default_factory=list)
    error: str | None = None
    response_time_ms: float = 0.0


@dataclass
class DeviceStats:
    connected: bool = False
    reads: int = 0
    writes: int = 0
    errors: int = 0
    last_error: str | None = None
    last_poll_at: datetime | None = None


class ModbusDevice(abc.ABC):
    def __init__(self, config: ModbusDeviceConfig) -> None:
        self.config = config
        self.stats = DeviceStats()

    @property
    def name(self) -> str:
        return self.config.name

    @abc.abstractmethod
    async def connect(self) -> None: ...

    @abc.abstractmethod
    async def disconnect(self) -> None: ...

    @abc.abstractmethod
    async def read(
        self, unit_id: int, area: RegisterArea, address: int, count: int
    ) -> ReadResult: ...

    @abc.abstractmethod
    async def write(
        self, unit_id: int, area: RegisterArea, address: int, values: list[int]
    ) -> ReadResult: ...


class ModbusEngine:
    """Registry of Modbus devices by name."""

    def __init__(self) -> None:
        self._devices: dict[str, ModbusDevice] = {}

    def register(self, device: ModbusDevice) -> None:
        self._devices[device.name] = device

    def get(self, name: str) -> ModbusDevice:
        return self._devices[name]

    def all_devices(self) -> list[ModbusDevice]:
        return list(self._devices.values())

    async def connect_all(self) -> None:
        for dev in self._devices.values():
            if not dev.config.enabled:
                continue
            try:
                await dev.connect()
            except Exception as exc:  # noqa: BLE001
                dev.stats.connected = False
                dev.stats.errors += 1
                dev.stats.last_error = str(exc)
                logger.warning("Modbus device %s connect failed: %s", dev.name, exc)

    async def disconnect_all(self) -> None:
        for dev in self._devices.values():
            await dev.disconnect()

    def status(self) -> list[dict[str, Any]]:
        return [
            {
                "name": d.name,
                "mode": d.config.mode.value,
                "enabled": d.config.enabled,
                "connected": d.stats.connected,
                "reads": d.stats.reads,
                "errors": d.stats.errors,
                "last_error": d.stats.last_error,
            }
            for d in self._devices.values()
        ]
