# Copyright (c) 2026 Aman Anand, M (T&I), Barauni
"""Modbus simulator device (in-process)."""

from __future__ import annotations

import asyncio

from app.core.config_schema import ModbusDeviceConfig
from app.core.enums import RegisterArea
from app.modbus.base import ModbusDevice, ReadResult
from app.simulator.modbus_memory import ModbusMemory


class ModbusSimulatorDevice(ModbusDevice):
    def __init__(self, config: ModbusDeviceConfig, memory: ModbusMemory | None = None) -> None:
        super().__init__(config)
        self._memory = memory or ModbusMemory()
        self._memory.seed_demo()

    async def connect(self) -> None:
        await asyncio.sleep(0)
        self.stats.connected = True

    async def disconnect(self) -> None:
        self.stats.connected = False

    async def read(
        self, unit_id: int, area: RegisterArea, address: int, count: int
    ) -> ReadResult:
        await asyncio.sleep(0)
        regs = self._memory.read(unit_id, area, address, count)
        self.stats.reads += 1
        return ReadResult(ok=True, registers=regs)

    async def write(
        self, unit_id: int, area: RegisterArea, address: int, values: list[int]
    ) -> ReadResult:
        await asyncio.sleep(0)
        try:
            self._memory.write(unit_id, area, address, values)
            self.stats.writes += 1
            return ReadResult(ok=True, registers=values)
        except Exception as exc:  # noqa: BLE001
            return ReadResult(ok=False, error=str(exc))
