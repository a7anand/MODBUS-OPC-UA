# Copyright (c) 2026 Aman Anand, M (T&I), Barauni
"""Poll scheduler — groups and intervals, not one thread per tag."""

from __future__ import annotations

import asyncio
import logging
from collections import defaultdict
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Callable

from app.core.datatype_engine import decode_tag_value, encode_tag_value
from app.core.addressing import function_to_area
from app.core.enums import RegisterArea, TagQuality
from app.core.mapping_engine import MappingEngine
from app.core.poll_batch import ReadBatch, plan_read_batches
from app.core.tag_database import TagDatabase
from app.modbus.frame_codec import read_exchange_hex

if TYPE_CHECKING:
    from app.modbus.base import ModbusEngine
    from app.opcua.server import OpcUaServerEngine

logger = logging.getLogger(__name__)


class PollScheduler:
    def __init__(
        self,
        tags: TagDatabase,
        modbus: ModbusEngine,
        mapping: MappingEngine,
        poll_intervals: dict[str, int],
        on_comm: Callable[..., None] | None = None,
    ) -> None:
        self._tags = tags
        self._modbus = modbus
        self._mapping = mapping
        self._intervals = poll_intervals
        self._on_comm = on_comm
        self._tasks: list[asyncio.Task] = []
        self._running = False
        self._opcua: OpcUaServerEngine | None = None
        self._fail_counts: dict[str, int] = {}

    def set_opcua(self, opcua: OpcUaServerEngine) -> None:
        self._opcua = opcua

    def start(self) -> None:
        self._running = True
        by_group: dict[str, list] = defaultdict(list)
        for rec in self._tags:
            if not rec.enabled:
                continue
            by_group[rec.definition.poll_group].append(rec)
        for group_id, records in by_group.items():
            interval = self._intervals.get(group_id, 1000)
            self._tasks.append(
                asyncio.create_task(self._loop(group_id, records, interval))
            )

    async def stop(self) -> None:
        self._running = False
        for task in self._tasks:
            task.cancel()
        await asyncio.gather(*self._tasks, return_exceptions=True)
        self._tasks.clear()

    async def _loop(self, group_id: str, records: list, interval_ms: int) -> None:
        while self._running:
            started = datetime.now(timezone.utc)
            errors = 0
            total = len(records)
            for batch in plan_read_batches(records):
                if len(batch.records) == 1:
                    await self._poll_one(batch.records[0])
                    continue
                try:
                    await self._poll_batch(batch)
                except Exception:  # noqa: BLE001
                    errors += len(batch.records)
                    for rec in batch.records:
                        await self._poll_one(rec)
            elapsed = (datetime.now(timezone.utc) - started).total_seconds() * 1000
            await asyncio.sleep(max(0, (interval_ms - elapsed) / 1000))

    async def _poll_batch(self, batch: ReadBatch) -> None:
        area = function_to_area(batch.function)
        device = self._modbus.get(batch.device)
        if not device.config.enabled:
            return
        fn = int(batch.function)
        tx_hex, _ = read_exchange_hex(
            batch.unit_id,
            fn,
            batch.start_internal,
            batch.register_count,
            None,
            False,
        )
        result = await device.read(
            batch.unit_id,
            area,
            batch.start_internal,
            batch.register_count,
        )
        _, rx_hex = read_exchange_hex(
            batch.unit_id,
            fn,
            batch.start_internal,
            batch.register_count,
            result.registers if result.ok else None,
            result.ok,
        )
        if not result.ok:
            for rec in batch.records:
                if self._on_comm:
                    self._on_comm(
                        protocol="MODBUS",
                        device=rec.definition.device,
                        tag_name=rec.definition.name,
                        direction="RX",
                        operation="poll_batch",
                        address=rec.address_display,
                        value=None,
                        ok=False,
                        response_ms=result.response_time_ms,
                        error=result.error,
                        tx_hex=tx_hex,
                        rx_hex=rx_hex,
                    )
                q = self._mapping.quality_for_read_ok(rec.definition.name, False)
                self._tags.update_value(rec.definition.name, rec.value, q, origin="modbus_poll")
            return
        base = batch.start_internal
        for rec in batch.records:
            offset = rec.address_internal - base
            slice_regs = result.registers[offset : offset + rec.definition.register_count]
            try:
                value = decode_tag_value(slice_regs, rec.definition)
            except Exception as exc:  # noqa: BLE001
                logger.warning("Batch decode failed %s: %s", rec.definition.name, exc)
                self._tags.update_value(
                    rec.definition.name, rec.value, TagQuality.BAD, origin="modbus_poll"
                )
                continue
            if self._on_comm:
                self._on_comm(
                    protocol="MODBUS",
                    device=rec.definition.device,
                    tag_name=rec.definition.name,
                    direction="RX",
                    operation="poll_batch",
                    address=rec.address_display,
                    value=value,
                    ok=True,
                    response_ms=result.response_time_ms,
                    error=None,
                    tx_hex=tx_hex,
                    rx_hex=rx_hex,
                )
            self._tags.update_value(
                rec.definition.name,
                value,
                TagQuality.GOOD,
                origin="modbus_poll",
                registers=slice_regs,
            )
            if self._mapping.should_publish(rec.definition.name, value, "modbus_poll"):
                if self._opcua:
                    await self._opcua.update_from_tag(rec.definition.name)

    async def _poll_one(self, rec) -> None:
        # One tag poll: Modbus read → decode → tag DB → OPC UA mirror.
        area = rec.definition.area or function_to_area(rec.definition.function)
        device = self._modbus.get(rec.definition.device)
        if not device.config.enabled:
            return
        fn = int(rec.definition.function)
        tx_hex, _ = read_exchange_hex(
            rec.definition.unit_id,
            fn,
            rec.address_internal,
            rec.definition.register_count,
            None,
            False,
        )
        result = await device.read(
            rec.definition.unit_id,
            area,
            rec.address_internal,
            rec.definition.register_count,
        )
        _, rx_hex = read_exchange_hex(
            rec.definition.unit_id,
            fn,
            rec.address_internal,
            rec.definition.register_count,
            result.registers if result.ok else None,
            result.ok,
        )
        if not result.ok:
            if self._on_comm:
                self._on_comm(
                    protocol="MODBUS",
                    device=rec.definition.device,
                    tag_name=rec.definition.name,
                    direction="RX",
                    operation="poll",
                    address=rec.address_display,
                    value=None,
                    ok=False,
                    response_ms=result.response_time_ms,
                    error=result.error,
                    tx_hex=tx_hex,
                    rx_hex=rx_hex,
                )
            name = rec.definition.name
            fails = self._fail_counts.get(name, 0) + 1
            self._fail_counts[name] = fails
            q = self._mapping.quality_for_read_ok(name, False)
            if fails >= 3:
                q = TagQuality.STALE
            self._tags.update_value(name, rec.value, q, origin="modbus_poll")
            return
        try:
            value = decode_tag_value(result.registers, rec.definition)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Decode failed %s: %s", rec.definition.name, exc)
            self._tags.update_value(
                rec.definition.name, rec.value, TagQuality.BAD, origin="modbus_poll"
            )
            return
        if self._on_comm:
            self._on_comm(
                protocol="MODBUS",
                device=rec.definition.device,
                tag_name=rec.definition.name,
                direction="RX",
                operation="poll",
                address=rec.address_display,
                value=value,
                ok=True,
                response_ms=result.response_time_ms,
                error=None,
                tx_hex=tx_hex,
                rx_hex=rx_hex,
            )
        self._fail_counts[rec.definition.name] = 0
        self._tags.update_value(
            rec.definition.name,
            value,
            TagQuality.GOOD,
            origin="modbus_poll",
            registers=result.registers,
        )
        if self._mapping.should_publish(rec.definition.name, value, "modbus_poll"):
            if self._opcua:
                await self._opcua.update_from_tag(rec.definition.name)

    async def write_tag(self, name: str, value, origin: str = "opcua_write") -> bool:
        rec = self._tags.get(name)
        if rec is None or not rec.definition.writable:
            return False
        area = rec.definition.area or function_to_area(rec.definition.function)
        regs = encode_tag_value(value, rec.definition)
        device = self._modbus.get(rec.definition.device)
        result = await device.write(
            rec.definition.unit_id, area, rec.address_internal, regs
        )
        if result.ok:
            self._tags.update_value(name, value, TagQuality.GOOD, origin=origin)
        return result.ok
