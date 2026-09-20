# Copyright (c) 2026 Aman Anand, M (T&I), Barauni
"""Central tag database — single source of truth."""

from __future__ import annotations

import threading
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Iterator

from app.core.config_schema import GatewayDocument, TagDefinition
from app.core.addressing import external_to_internal, function_to_area
from app.core.enums import ModbusDeviceMode, TagQuality
from app.core.tag_history import TagHistoryBuffer
from app.core.trend_buffer import TrendBuffer


@dataclass
class TagRecord:
    definition: TagDefinition
    value: Any = None
    quality: TagQuality = TagQuality.BAD
    timestamp: datetime | None = None
    source_timestamp: datetime | None = None
    source_device: str = ""
    source_protocol: str = ""
    address_internal: int = 0
    address_display: int = 0
    last_write_origin: str = ""
    enabled: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.definition.name,
            "description": self.definition.description,
            "datatype": self.definition.datatype.value,
            "value": self.value,
            "quality": self.quality.value,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "source_timestamp": (
                self.source_timestamp.isoformat() if self.source_timestamp else None
            ),
            "device": self.definition.device,
            "protocol": self.definition.protocol,
            "address_display": self.address_display,
            "address_internal": self.address_internal,
            "opcua_node": self.definition.opcua_node,
            "engineering_unit": self.definition.engineering_unit,
            "enabled": self.enabled,
        }


class TagDatabase:
    def __init__(
        self,
        trends: TrendBuffer | None = None,
        history: TagHistoryBuffer | None = None,
    ) -> None:
        self._lock = threading.RLock()
        self._tags: dict[str, TagRecord] = {}
        self._trends = trends
        self._history = history

    def build_from_config(self, doc: GatewayDocument) -> None:
        devices = {d.name: d for d in doc.modbus.devices}
        with self._lock:
            self._tags.clear()
            for tag_def in doc.tags:
                dev = devices.get(tag_def.device)
                from app.core.enums import AddressBase

                base = dev.address_base if dev else AddressBase.ONE
                area = tag_def.area or function_to_area(tag_def.function)
                internal, display = external_to_internal(
                    tag_def.address, base, area
                )
                tag_def.area = area
                tag_def.address_internal = internal
                tag_def.address_display = display
                protocol = "MODBUS_SIMULATOR"
                if dev:
                    if dev.mode == ModbusDeviceMode.SIMULATOR:
                        protocol = "MODBUS_SIMULATOR"
                    elif dev.mode in (
                        ModbusDeviceMode.TCP_CLIENT,
                        ModbusDeviceMode.TCP_SERVER,
                    ):
                        protocol = "MODBUS_TCP"
                    else:
                        protocol = "MODBUS_RTU"
                record = TagRecord(
                    definition=tag_def,
                    quality=TagQuality.BAD,
                    source_device=tag_def.device,
                    source_protocol=protocol,
                    address_internal=internal,
                    address_display=display,
                    enabled=tag_def.enabled,
                )
                self._tags[tag_def.name] = record

    def get(self, name: str) -> TagRecord | None:
        with self._lock:
            return self._tags.get(name)

    def update_value(
        self,
        name: str,
        value: Any,
        quality: TagQuality,
        origin: str = "poll",
        registers: list[int] | None = None,
    ) -> None:
        now = datetime.now(timezone.utc)
        with self._lock:
            rec = self._tags.get(name)
            if rec is None:
                return
            rec.value = value
            rec.quality = quality
            rec.timestamp = now
            rec.source_timestamp = now
            rec.last_write_origin = origin
            if quality == TagQuality.GOOD:
                if self._trends is not None:
                    self._trends.record(name, value)
                if self._history is not None:
                    self._history.record(rec.definition, value, registers)

    def snapshot(self) -> list[dict[str, Any]]:
        with self._lock:
            return [t.to_dict() for t in self._tags.values()]

    def __iter__(self) -> Iterator[TagRecord]:
        with self._lock:
            return iter(list(self._tags.values()))

    def names(self) -> list[str]:
        with self._lock:
            return list(self._tags.keys())
