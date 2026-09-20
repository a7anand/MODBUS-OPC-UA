# Copyright (c) 2026 Aman Anand, M (T&I), Barauni
"""Modbus client pool (TCP, RTU, and built-in simulator)."""

from __future__ import annotations

import asyncio
import logging
import math
import time
from dataclasses import dataclass, field
from typing import Any

from pymodbus.client import AsyncModbusSerialClient, AsyncModbusTcpClient
from pymodbus.exceptions import ModbusException

from gateway.config import ModbusConnectionConfig, ModbusTransport, RegisterArea

logger = logging.getLogger(__name__)


@dataclass
class ReadResult:
    ok: bool
    registers: list[int] = field(default_factory=list)
    error: str | None = None


class ModbusSimulator:
    """In-process Modbus memory for demo and CI without external hardware."""

    def __init__(self) -> None:
        self._coils: dict[tuple[int, int], bool] = {}
        self._discrete: dict[tuple[int, int], bool] = {}
        self._holding: dict[tuple[int, int], int] = {}
        self._input: dict[tuple[int, int], int] = {}
        self._seed_defaults()

    def _seed_defaults(self) -> None:
        for uid in (1, 2):
            self._holding[(uid, 0)] = 2500  # 25.00 °C scaled x100
            self._holding[(uid, 1)] = 1013
            self._input[(uid, 0)] = 4096
            self._coils[(uid, 0)] = True

    def _wave(self, t: float, uid: int) -> int:
        return int(2000 + 500 * math.sin(t / 5 + uid))

    async def read(
        self, unit_id: int, area: RegisterArea, address: int, count: int
    ) -> ReadResult:
        await asyncio.sleep(0)
        t = time.time()
        values: list[int] = []
        for i in range(count):
            if area == RegisterArea.COIL:
                values.append(1 if self._coils.get((unit_id, address + i), False) else 0)
            elif area == RegisterArea.DISCRETE_INPUT:
                values.append(1 if self._discrete.get((unit_id, address + i), False) else 0)
            elif area == RegisterArea.HOLDING_REGISTER:
                base = self._holding.get((unit_id, address + i))
                if base is None and i == 0:
                    base = self._wave(t, unit_id)
                values.append(base if base is not None else 0)
            elif area == RegisterArea.INPUT_REGISTER:
                values.append(self._input.get((unit_id, address + i), 1000 + i))
            else:
                return ReadResult(ok=False, error=f"Unsupported area {area}")
        return ReadResult(ok=True, registers=values)

    async def write(
        self, unit_id: int, area: RegisterArea, address: int, values: list[int]
    ) -> ReadResult:
        await asyncio.sleep(0)
        if area == RegisterArea.COIL:
            for i, v in enumerate(values):
                self._coils[(unit_id, address + i)] = bool(v)
        elif area == RegisterArea.HOLDING_REGISTER:
            for i, v in enumerate(values):
                self._holding[(unit_id, address + i)] = v & 0xFFFF
        else:
            return ReadResult(ok=False, error=f"Area {area} is read-only")
        return ReadResult(ok=True, registers=values)


class ModbusConnection:
    def __init__(self, config: ModbusConnectionConfig) -> None:
        self.config = config
        self._client: Any = None
        self._simulator = ModbusSimulator() if config.transport == ModbusTransport.SIMULATOR else None
        self._lock = asyncio.Lock()

    async def connect(self) -> None:
        if self._simulator is not None:
            return
        if self.config.transport == ModbusTransport.TCP:
            tcp = self.config.tcp
            assert tcp is not None
            self._client = AsyncModbusTcpClient(
                host=tcp.host,
                port=tcp.port,
                timeout=self.config.request_timeout_sec,
            )
        elif self.config.transport == ModbusTransport.RTU:
            rtu = self.config.rtu
            assert rtu is not None
            self._client = AsyncModbusSerialClient(
                port=rtu.port,
                baudrate=rtu.baudrate,
                bytesize=rtu.bytesize,
                parity=rtu.parity,
                stopbits=rtu.stopbits,
                timeout=rtu.timeout_sec,
            )
        else:
            raise ValueError(f"Unknown transport {self.config.transport}")

        connected = await self._client.connect()
        if not connected:
            raise ConnectionError(
                f"Modbus connection {self.config.id} failed to connect"
            )
        logger.info("Modbus connection %s connected", self.config.id)

    async def close(self) -> None:
        if self._client is not None:
            self._client.close()
            self._client = None

    async def read_registers(
        self, unit_id: int, area: RegisterArea, address: int, count: int
    ) -> ReadResult:
        if self._simulator is not None:
            return await self._simulator.read(unit_id, area, address, count)

        async with self._lock:
            try:
                if area == RegisterArea.COIL:
                    rr = await self._client.read_coils(address, count=count, device_id=unit_id)
                    if rr.isError():
                        return ReadResult(ok=False, error=str(rr))
                    bits = rr.bits[:count]
                    return ReadResult(ok=True, registers=[1 if b else 0 for b in bits])
                if area == RegisterArea.DISCRETE_INPUT:
                    rr = await self._client.read_discrete_inputs(
                        address, count=count, device_id=unit_id
                    )
                    if rr.isError():
                        return ReadResult(ok=False, error=str(rr))
                    bits = rr.bits[:count]
                    return ReadResult(ok=True, registers=[1 if b else 0 for b in bits])
                if area == RegisterArea.HOLDING_REGISTER:
                    rr = await self._client.read_holding_registers(
                        address, count=count, device_id=unit_id
                    )
                    if rr.isError():
                        return ReadResult(ok=False, error=str(rr))
                    return ReadResult(ok=True, registers=list(rr.registers))
                if area == RegisterArea.INPUT_REGISTER:
                    rr = await self._client.read_input_registers(
                        address, count=count, device_id=unit_id
                    )
                    if rr.isError():
                        return ReadResult(ok=False, error=str(rr))
                    return ReadResult(ok=True, registers=list(rr.registers))
                return ReadResult(ok=False, error=f"Unsupported area {area}")
            except ModbusException as exc:
                return ReadResult(ok=False, error=str(exc))
            except Exception as exc:  # noqa: BLE001
                return ReadResult(ok=False, error=str(exc))

    async def write_registers(
        self, unit_id: int, area: RegisterArea, address: int, values: list[int]
    ) -> ReadResult:
        if self._simulator is not None:
            return await self._simulator.write(unit_id, area, address, values)

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
                    return ReadResult(ok=False, error=f"Area {area} is read-only")
                if rr.isError():
                    return ReadResult(ok=False, error=str(rr))
                return ReadResult(ok=True, registers=values)
            except ModbusException as exc:
                return ReadResult(ok=False, error=str(exc))
            except Exception as exc:  # noqa: BLE001
                return ReadResult(ok=False, error=str(exc))


class ModbusPool:
    def __init__(self, connections: list[ModbusConnectionConfig]) -> None:
        self._connections = {c.id: ModbusConnection(c) for c in connections}

    async def connect_all(self) -> None:
        for conn in self._connections.values():
            await conn.connect()

    async def close_all(self) -> None:
        for conn in self._connections.values():
            await conn.close()

    def get(self, connection_id: str) -> ModbusConnection:
        return self._connections[connection_id]
