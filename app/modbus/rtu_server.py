# Copyright (c) 2026 Aman Anand, M (T&I), Barauni
"""Modbus RTU server — memory-backed (serial server optional on host)."""

from __future__ import annotations

from app.core.config_schema import ModbusDeviceConfig
from app.core.enums import RegisterArea
from app.modbus.base import ModbusDevice, ReadResult
from app.modbus.simulator_device import ModbusSimulatorDevice
from app.simulator.modbus_memory import ModbusMemory


class ModbusRtuServerDevice(ModbusDevice):
    """RTU server uses shared memory; serial listener is host-dependent."""

    def __init__(self, config: ModbusDeviceConfig, memory: ModbusMemory) -> None:
        super().__init__(config)
        self._inner = ModbusSimulatorDevice(config, memory)

    async def connect(self) -> None:
        await self._inner.connect()
        self.stats.connected = self._inner.stats.connected

    async def disconnect(self) -> None:
        await self._inner.disconnect()
        self.stats.connected = False

    async def read(
        self, unit_id: int, area: RegisterArea, address: int, count: int
    ) -> ReadResult:
        return await self._inner.read(unit_id, area, address, count)

    async def write(
        self, unit_id: int, area: RegisterArea, address: int, values: list[int]
    ) -> ReadResult:
        return await self._inner.write(unit_id, area, address, values)
