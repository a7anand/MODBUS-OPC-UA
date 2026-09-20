# Copyright (c) 2026 Aman Anand, M (T&I), Barauni
"""Modbus TCP client."""

from __future__ import annotations

import asyncio
import time

from pymodbus.client import AsyncModbusTcpClient
from pymodbus.exceptions import ModbusException

from app.core.config_schema import ModbusDeviceConfig
from app.core.enums import RegisterArea
from app.modbus.base import ModbusDevice, ReadResult


class ModbusTcpClientDevice(ModbusDevice):
    def __init__(self, config: ModbusDeviceConfig) -> None:
        super().__init__(config)
        self._client: AsyncModbusTcpClient | None = None
        self._lock = asyncio.Lock()

    async def connect(self) -> None:
        self._client = AsyncModbusTcpClient(
            host=self.config.host,
            port=self.config.port,
            timeout=self.config.response_timeout_sec,
        )
        ok = await self._client.connect()
        self.stats.connected = bool(ok)
        if not ok:
            raise ConnectionError(f"Modbus TCP {self.name} connect failed")

    async def disconnect(self) -> None:
        if self._client:
            self._client.close()
        self._client = None
        self.stats.connected = False

    async def read(
        self, unit_id: int, area: RegisterArea, address: int, count: int
    ) -> ReadResult:
        if not self._client:
            return ReadResult(ok=False, error="not connected")
        start = time.perf_counter()
        async with self._lock:
            try:
                if area == RegisterArea.COIL:
                    rr = await self._client.read_coils(address, count=count, device_id=unit_id)
                    if rr.isError():
                        self.stats.errors += 1
                        return ReadResult(ok=False, error=str(rr))
                    bits = rr.bits[:count]
                    regs = [1 if b else 0 for b in bits]
                elif area == RegisterArea.DISCRETE_INPUT:
                    rr = await self._client.read_discrete_inputs(
                        address, count=count, device_id=unit_id
                    )
                    if rr.isError():
                        self.stats.errors += 1
                        return ReadResult(ok=False, error=str(rr))
                    regs = [1 if b else 0 for b in rr.bits[:count]]
                elif area == RegisterArea.HOLDING_REGISTER:
                    rr = await self._client.read_holding_registers(
                        address, count=count, device_id=unit_id
                    )
                    if rr.isError():
                        self.stats.errors += 1
                        return ReadResult(ok=False, error=str(rr))
                    regs = list(rr.registers)
                else:
                    rr = await self._client.read_input_registers(
                        address, count=count, device_id=unit_id
                    )
                    if rr.isError():
                        self.stats.errors += 1
                        return ReadResult(ok=False, error=str(rr))
                    regs = list(rr.registers)
                self.stats.reads += 1
                ms = (time.perf_counter() - start) * 1000
                return ReadResult(ok=True, registers=regs, response_time_ms=ms)
            except ModbusException as exc:
                self.stats.errors += 1
                self.stats.last_error = str(exc)
                return ReadResult(ok=False, error=str(exc))
            except Exception as exc:  # noqa: BLE001
                self.stats.errors += 1
                self.stats.last_error = str(exc)
                return ReadResult(ok=False, error=str(exc))

    async def write(
        self, unit_id: int, area: RegisterArea, address: int, values: list[int]
    ) -> ReadResult:
        if not self._client:
            return ReadResult(ok=False, error="not connected")
        async with self._lock:
            try:
                if area == RegisterArea.COIL:
                    if len(values) == 1:
                        rr = await self._client.write_coil(
                            address, bool(values[0]), device_id=unit_id
                        )
                    else:
                        rr = await self._client.write_coils(
                            address, [bool(v) for v in values], device_id=unit_id
                        )
                elif area == RegisterArea.HOLDING_REGISTER:
                    if len(values) == 1:
                        rr = await self._client.write_register(
                            address, values[0], device_id=unit_id
                        )
                    else:
                        rr = await self._client.write_registers(
                            address, values, device_id=unit_id
                        )
                else:
                    return ReadResult(ok=False, error="read-only area")
                if rr.isError():
                    self.stats.errors += 1
                    return ReadResult(ok=False, error=str(rr))
                self.stats.writes += 1
                return ReadResult(ok=True, registers=values)
            except Exception as exc:  # noqa: BLE001
                self.stats.errors += 1
                return ReadResult(ok=False, error=str(exc))
