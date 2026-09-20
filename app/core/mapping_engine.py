# Copyright (c) 2026 Aman Anand, M (T&I), Barauni
"""Mapping between Modbus-sourced tags and OPC UA (and reverse)."""

from __future__ import annotations

from app.core.config_schema import GatewayDocument, MappingDefinition
from app.core.enums import MappingDirection, TagQuality
from app.core.tag_database import TagDatabase


class MappingEngine:
    def __init__(self, doc: GatewayDocument, tags: TagDatabase) -> None:
        self._doc = doc
        self._tags = tags
        self._mappings: dict[str, MappingDefinition] = {
            m.id: m for m in doc.mappings
        }

    def should_publish(self, tag_name: str, new_value: float | int, origin: str) -> bool:
        """Gate OPC UA updates (deadband / direction). Tag DB always updates on poll."""
        rec = self._tags.get(tag_name)
        if rec is None:
            return False
        deadband = rec.definition.deadband
        if deadband and rec.value is not None:
            try:
                if abs(float(new_value) - float(rec.value)) < deadband:
                    return False
            except (TypeError, ValueError):
                pass
        mapping = self._mapping_for_tag(tag_name)
        if mapping and not mapping.enabled:
            return False
        direction = rec.definition.direction
        if mapping:
            direction = mapping.direction
        if direction == MappingDirection.UA_TO_MB and origin == "modbus_poll":
            return False
        return True

    def _mapping_for_tag(self, tag_name: str) -> MappingDefinition | None:
        for m in self._mappings.values():
            if m.tag_name == tag_name:
                return m
        return None

    def quality_for_read_ok(self, tag_name: str, ok: bool) -> TagQuality:
        return TagQuality.GOOD if ok else TagQuality.COMMUNICATION_FAILURE
