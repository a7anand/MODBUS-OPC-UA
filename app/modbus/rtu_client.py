# Copyright (c) 2026 Aman Anand, M (T&I), Barauni
"""Modbus RTU client."""

from __future__ import annotations

import asyncio
import time

from pymodbus.client import AsyncModbusSerialClient
from pymodbus.exceptions import ModbusException

from app.core.config_schema import ModbusDeviceConfig
from app.core.enums import RegisterArea
from app.modbus.base import ModbusDevice, ReadResult
from app.modbus.tcp_client import ModbusTcpClientDevice


class ModbusRtuClientDevice(ModbusDevice):
    """RTU client — same read/write logic as TCP with serial transport."""

    def __init__(self, config: ModbusDeviceConfig) -> None:
        super().__init__(config)
        self._client: AsyncModbusSerialClient | None = None
        self._lock = asyncio.Lock()
        self._tcp_helper = ModbusTcpClientDevice(config)

    async def connect(self) -> None:
        self._client = AsyncModbusSerialClient(
            port=self.config.serial_port,
            baudrate=self.config.baudrate,
            bytesize=self.config.bytesize,
            parity=self.config.parity,
            stopbits=self.config.stopbits,
            timeout=self.config.response_timeout_sec,
        )
        ok = await self._client.connect()
        self.stats.connected = bool(ok)
        self._tcp_helper._client = self._client  # type: ignore[assignment]
        if not ok:
            raise ConnectionError(f"Modbus RTU {self.name} connect failed")

    async def disconnect(self) -> None:
        if self._client:
            self._client.close()
        self._client = None
        self.stats.connected = False

    async def read(
        self, unit_id: int, area: RegisterArea, address: int, count: int
    ) -> ReadResult:
        self._tcp_helper._client = self._client
        self._tcp_helper.stats = self.stats
        return await self._tcp_helper.read(unit_id, area, address, count)

    async def write(
        self, unit_id: int, area: RegisterArea, address: int, values: list[int]
    ) -> ReadResult:
        self._tcp_helper._client = self._client
        self._tcp_helper.stats = self.stats
        return await self._tcp_helper.write(unit_id, area, address, values)
