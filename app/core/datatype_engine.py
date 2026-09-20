# Copyright (c) 2026 Aman Anand, M (T&I), Barauni
"""Facade over register codec for Core consumers."""

from __future__ import annotations

from typing import Any

from app.core.config_schema import TagDefinition
from app.modbus.register_codec import decode_registers, encode_registers


def decode_tag_value(registers: list[int], tag: TagDefinition) -> Any:
    return decode_registers(registers, tag)


def encode_tag_value(value: Any, tag: TagDefinition) -> list[int]:
    return encode_registers(value, tag)
