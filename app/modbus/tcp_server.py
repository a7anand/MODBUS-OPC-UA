# Copyright (c) 2026 Aman Anand, M (T&I), Barauni
"""Modbus TCP server backed by shared memory."""

from __future__ import annotations

import asyncio
import logging

from pymodbus.datastore import ModbusSequentialDataBlock, ModbusServerContext
from pymodbus.datastore.context import ModbusDeviceContext
from pymodbus.server import StartAsyncTcpServer

from app.core.config_schema import ModbusDeviceConfig
from app.core.enums import RegisterArea
from app.modbus.base import ModbusDevice, ReadResult
from app.simulator.modbus_memory import ModbusMemory

logger = logging.getLogger(__name__)


class ModbusTcpServerDevice(ModbusDevice):
    def __init__(self, config: ModbusDeviceConfig, memory: ModbusMemory) -> None:
        super().__init__(config)
        self._memory = memory
        self._server_task: asyncio.Task | None = None
        self._unit_id = config.unit_id

    async def connect(self) -> None:
        store = ModbusDeviceContext(
            di=ModbusSequentialDataBlock(0, [0] * 10000),
            co=ModbusSequentialDataBlock(0, [0] * 10000),
            hr=ModbusSequentialDataBlock(0, [0] * 10000),
            ir=ModbusSequentialDataBlock(0, [0] * 10000),
        )
        context = ModbusServerContext(devices=store, single=True)

        async def _run() -> None:
            await StartAsyncTcpServer(
                context=context,
                address=(self.config.host, self.config.port),
            )

        self._server_task = asyncio.create_task(_run())
        self.stats.connected = True
        logger.info("Modbus TCP server %s on %s:%s", self.name, self.config.host, self.config.port)

    async def disconnect(self) -> None:
        if self._server_task:
            self._server_task.cancel()
            try:
                await self._server_task
            except asyncio.CancelledError:
                pass
        self.stats.connected = False

    async def read(
        self, unit_id: int, area: RegisterArea, address: int, count: int
    ) -> ReadResult:
        regs = self._memory.read(unit_id, area, address, count)
        return ReadResult(ok=True, registers=regs)

    async def write(
        self, unit_id: int, area: RegisterArea, address: int, values: list[int]
    ) -> ReadResult:
        self._memory.write(unit_id, area, address, values)
        return ReadResult(ok=True, registers=values)
