# Copyright (c) 2026 Aman Anand, M (T&I), Barauni
"""Polling engine: groups tags by connection and poll interval."""

from __future__ import annotations

import asyncio
import logging
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone

from asyncua import ua

from gateway.config import GatewayConfig, RegisterArea, TagConfig
from gateway.modbus_client import ModbusPool
from gateway.opcua_bridge import OpcUaBridge

logger = logging.getLogger(__name__)


@dataclass
class PollStats:
    polls: int = 0
    errors: int = 0
    last_poll_at: datetime | None = None
    last_error: str | None = None


class Poller:
    def __init__(
        self,
        config: GatewayConfig,
        modbus: ModbusPool,
        opcua: OpcUaBridge,
    ) -> None:
        self._config = config
        self._modbus = modbus
        self._opcua = opcua
        self._tasks: list[asyncio.Task] = []
        self.stats: dict[str, PollStats] = defaultdict(PollStats)
        self._running = False

    def start(self) -> None:
        self._running = True
        intervals = {g.id: g.interval_ms for g in self._config.poll_groups}
        by_group: dict[str, list[TagConfig]] = defaultdict(list)
        for tag in self._config.tags:
            by_group[tag.poll_group].append(tag)

        for group_id, tags in by_group.items():
            interval_ms = intervals.get(group_id, 1000)
            self._tasks.append(
                asyncio.create_task(self._poll_loop(group_id, tags, interval_ms))
            )

    async def stop(self) -> None:
        self._running = False
        for task in self._tasks:
            task.cancel()
        await asyncio.gather(*self._tasks, return_exceptions=True)
        self._tasks.clear()

    async def _poll_loop(
        self, group_id: str, tags: list[TagConfig], interval_ms: int
    ) -> None:
        while self._running:
            started = datetime.now(timezone.utc)
            for tag in tags:
                await self._poll_tag(group_id, tag)
            elapsed = (datetime.now(timezone.utc) - started).total_seconds() * 1000
            sleep_ms = max(0, interval_ms - elapsed)
            await asyncio.sleep(sleep_ms / 1000)

    async def _poll_tag(self, group_id: str, tag: TagConfig) -> None:
        stats = self.stats[group_id]
        stats.polls += 1
        stats.last_poll_at = datetime.now(timezone.utc)
        conn = self._modbus.get(tag.connection_id)
        result = await conn.read_registers(
            tag.unit_id, tag.area, tag.address, tag.length_registers
        )
        if not result.ok:
            stats.errors += 1
            stats.last_error = result.error
            await self._opcua.update_tag(
                tag.id, None, ua.StatusCode(ua.StatusCodes.BadCommunicationError)
            )
            logger.warning(
                "Poll failed tag=%s error=%s", tag.id, result.error
            )
            return
        await self._opcua.update_tag(
            tag.id, result.registers, ua.StatusCode(ua.StatusCodes.Good)
        )

    async def write_tag(self, tag_id: str, value) -> bool:
        tag = next((t for t in self._config.tags if t.id == tag_id), None)
        if tag is None or not tag.writable:
            return False
        if tag.area not in (RegisterArea.COIL, RegisterArea.HOLDING_REGISTER):
            return False
        registers = self._opcua.registers_for_write(tag_id, value)
        conn = self._modbus.get(tag.connection_id)
        result = await conn.write_registers(
            tag.unit_id, tag.area, tag.address, registers
        )
        if result.ok:
            await self._opcua.update_tag(
                tag_id, result.registers, ua.StatusCode(ua.StatusCodes.Good)
            )
        return result.ok
