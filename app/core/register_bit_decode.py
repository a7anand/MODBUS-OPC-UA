# Copyright (c) 2026 Aman Anand, M (T&I), Barauni
"""Decode holding-register words into per-bit boolean tags (4X:n.b style)."""

from __future__ import annotations

import re
from typing import Any

from app.core.config_schema import TagDefinition
from app.core.enums import DataType, ModbusFunction

_FOUR_X_BIT = re.compile(r"^4X:(\d+)\.(\d+)$", re.IGNORECASE)
_FOUR_X_REG = re.compile(r"^4X:(\d+)$", re.IGNORECASE)


def holding_plc_address(four_x_offset: int) -> int:
    """4X register offset (e.g. 11) → PLC holding address 40012."""
    return 40001 + four_x_offset


def parse_four_x_address(text: str) -> tuple[int, int | None]:
    """Parse `4X:11.3` or `4X:11` → (plc_address, bit_index or None)."""
    raw = text.strip()
    m = _FOUR_X_BIT.match(raw)
    if m:
        reg = int(m.group(1))
        bit = int(m.group(2))
        if bit > 15:
            raise ValueError("bit index must be 0–15")
        return holding_plc_address(reg), bit
    m = _FOUR_X_REG.match(raw)
    if m:
        return holding_plc_address(int(m.group(1))), None
    if raw.isdigit():
        n = int(raw)
        if n >= 40001:
            return n, None
        return holding_plc_address(n), None
    raise ValueError("Use PLC address (40012), 4X offset (4X:11), or 4X:11.3")


def decode_bit(register_value: int, bit_index: int) -> bool:
    return bool((register_value & 0xFFFF) >> bit_index & 1)


def set_bit(register_value: int, bit_index: int, value: bool) -> int:
    mask = 1 << bit_index
    word = register_value & 0xFFFF
    if value:
        return word | mask
    return word & ~mask


def preview_register_bits(register_value: int) -> list[dict[str, Any]]:
    word = register_value & 0xFFFF
    return [
        {"bit": i, "value": bool((word >> i) & 1), "binary": f"{(word >> i) & 1}"}
        for i in range(16)
    ]


def build_bool_tag(
    name: str,
    device: str,
    plc_address: int,
    bit_index: int,
    description: str = "",
    writable: bool = False,
    poll_group: str = "default",
) -> TagDefinition:
    return TagDefinition(
        name=name,
        description=description,
        device=device,
        function=ModbusFunction.READ_HOLDING,
        address=plc_address,
        register_count=1,
        datatype=DataType.BOOL,
        bit_index=bit_index,
        writable=writable,
        poll_group=poll_group,
    )
