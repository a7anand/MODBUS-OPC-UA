# Copyright (c) 2026 Aman Anand, M (T&I), Barauni
"""Register codec with explicit byte layouts."""

from __future__ import annotations

import struct
from typing import Any

from app.core.enums import ByteLayout, DataType, WordOrder
from app.core.scaling_engine import scale_to_engineering, scale_to_raw
from app.core.config_schema import TagDefinition


def _swap16(value: int) -> int:
    return ((value & 0xFF) << 8) | ((value >> 8) & 0xFF)


def _layout_to_byte_order(layout: ByteLayout) -> tuple[bool, bool]:
    """Return (swap_words_in_register, reverse_word_order)."""
    if layout == ByteLayout.ABCD:
        return False, False
    if layout == ByteLayout.BADC:
        return True, False
    if layout == ByteLayout.CDAB:
        return False, True
    return True, True


def _normalize_registers(
    registers: list[int], layout: ByteLayout, word_order: WordOrder
) -> bytes:
    swap_in_word, reverse_words = _layout_to_byte_order(layout)
    regs = list(registers)
    if swap_in_word:
        regs = [_swap16(r) for r in regs]
    raw = b"".join(struct.pack(">H", r & 0xFFFF) for r in regs)
    if word_order == WordOrder.LITTLE and len(regs) > 1:
        words = [raw[i : i + 2] for i in range(0, len(raw), 2)]
        raw = b"".join(reversed(words))
    if reverse_words and len(regs) > 1:
        words = [raw[i : i + 2] for i in range(0, len(raw), 2)]
        raw = b"".join(reversed(words))
    return raw


def decode_registers(registers: list[int], tag: TagDefinition) -> Any:
    dt = tag.datatype
    if dt == DataType.BOOL:
        return bool(registers[0] & 1) if registers else False
    raw = _normalize_registers(registers, tag.byte_order, tag.word_order)
    if dt == DataType.INT16:
        raw_val = struct.unpack(">h", raw[:2])[0]
    elif dt == DataType.UINT16:
        raw_val = struct.unpack(">H", raw[:2])[0]
    elif dt == DataType.INT32:
        raw_val = struct.unpack(">i", raw[:4])[0]
    elif dt == DataType.UINT32:
        raw_val = struct.unpack(">I", raw[:4])[0]
    elif dt == DataType.INT64:
        raw_val = struct.unpack(">q", raw[:8])[0]
    elif dt == DataType.UINT64:
        raw_val = struct.unpack(">Q", raw[:8])[0]
    elif dt == DataType.FLOAT32:
        raw_val = struct.unpack(">f", raw[:4])[0]
    elif dt == DataType.FLOAT64:
        raw_val = struct.unpack(">d", raw[:8])[0]
    elif dt == DataType.STRING:
        return raw.rstrip(b"\x00").decode("utf-8", errors="replace")
    else:
        raise ValueError(f"Unsupported datatype {dt}")
    if isinstance(raw_val, (int, float)):
        return scale_to_engineering(float(raw_val), tag)
    return raw_val


def encode_registers(value: Any, tag: TagDefinition) -> list[int]:
    dt = tag.datatype
    if dt == DataType.BOOL:
        return [1 if bool(value) else 0]
    if dt == DataType.STRING:
        raw = str(value).encode("utf-8")
        need = tag.register_count * 2
        raw = raw[:need].ljust(need, b"\x00")
        return [struct.unpack(">H", raw[i : i + 2])[0] for i in range(0, len(raw), 2)]
    eng = scale_to_raw(float(value), tag) if isinstance(value, (int, float)) else value
    if dt == DataType.INT16:
        raw = struct.pack(">h", int(eng))
    elif dt == DataType.UINT16:
        raw = struct.pack(">H", int(eng) & 0xFFFF)
    elif dt == DataType.INT32:
        raw = struct.pack(">i", int(eng))
    elif dt == DataType.UINT32:
        raw = struct.pack(">I", int(eng) & 0xFFFFFFFF)
    elif dt == DataType.INT64:
        raw = struct.pack(">q", int(eng))
    elif dt == DataType.UINT64:
        raw = struct.pack(">Q", int(eng))
    elif dt == DataType.FLOAT32:
        raw = struct.pack(">f", float(eng))
    elif dt == DataType.FLOAT64:
        raw = struct.pack(">d", float(eng))
    else:
        raise ValueError(f"Unsupported encode datatype {dt}")
    return [struct.unpack(">H", raw[i : i + 2])[0] for i in range(0, len(raw), 2)]


def diagnostic_interpretations(registers: list[int]) -> dict[str, Any]:
    raw = _normalize_registers(registers, ByteLayout.ABCD, WordOrder.BIG)
    out: dict[str, Any] = {
        "hex": " ".join(f"{r:04X}" for r in registers),
        "decimal": registers,
        "binary": [f"{r:016b}" for r in registers],
    }
    if len(raw) >= 2:
        out["int16_signed"] = struct.unpack(">h", raw[:2])[0]
        out["uint16"] = struct.unpack(">H", raw[:2])[0]
    if len(raw) >= 4:
        out["float32"] = struct.unpack(">f", raw[:4])[0]
        out["int32"] = struct.unpack(">i", raw[:4])[0]
    if len(raw) >= 8:
        out["float64"] = struct.unpack(">d", raw[:8])[0]
    try:
        out["ascii"] = raw.decode("ascii", errors="replace")
    except Exception:
        out["ascii"] = ""
    return out
