# Copyright (c) 2026 Aman Anand, M (T&I), Barauni
"""Decode and encode Modbus register payloads."""

from __future__ import annotations

import struct
from typing import Any

from gateway.config import ByteOrder, DataType, WordOrder


def _swap16(value: int) -> int:
    return ((value & 0xFF) << 8) | ((value >> 8) & 0xFF)


def _normalize_registers(
    registers: list[int], byte_order: ByteOrder, word_order: WordOrder
) -> bytes:
    regs = list(registers)
    if byte_order in (ByteOrder.BIG_SWAP, ByteOrder.LITTLE_SWAP):
        regs = [_swap16(r) for r in regs]
    raw = b"".join(struct.pack(">H", r & 0xFFFF) for r in regs)
    if byte_order == ByteOrder.LITTLE:
        # per-register little endian: swap bytes in each 16-bit word
        words = [raw[i : i + 2] for i in range(0, len(raw), 2)]
        raw = b"".join(w[::-1] for w in words)
    if word_order == WordOrder.LITTLE and len(regs) > 1:
        words = [raw[i : i + 2] for i in range(0, len(raw), 2)]
        raw = b"".join(reversed(words))
    return raw


def decode_value(
    registers: list[int],
    data_type: DataType,
    byte_order: ByteOrder,
    word_order: WordOrder,
    scale: float,
    offset: float,
) -> Any:
    if data_type == DataType.BOOL:
        return bool(registers[0] & 1) if registers else False

    raw = _normalize_registers(registers, byte_order, word_order)

    if data_type == DataType.INT16:
        value = struct.unpack(">h", raw[:2])[0]
    elif data_type == DataType.UINT16:
        value = struct.unpack(">H", raw[:2])[0]
    elif data_type == DataType.INT32:
        value = struct.unpack(">i", raw[:4])[0]
    elif data_type == DataType.UINT32:
        value = struct.unpack(">I", raw[:4])[0]
    elif data_type == DataType.FLOAT32:
        value = struct.unpack(">f", raw[:4])[0]
    elif data_type == DataType.FLOAT64:
        value = struct.unpack(">d", raw[:8])[0]
    elif data_type == DataType.STRING:
        value = raw.rstrip(b"\x00").decode("utf-8", errors="replace")
        return value
    else:
        raise ValueError(f"Unsupported data type: {data_type}")

    return value * scale + offset


def encode_value(
    value: Any,
    data_type: DataType,
    byte_order: ByteOrder,
    word_order: WordOrder,
    scale: float,
    offset: float,
    length_registers: int,
) -> list[int]:
    if data_type == DataType.BOOL:
        return [1 if bool(value) else 0]

    if data_type == DataType.STRING:
        raw = str(value).encode("utf-8")
        need = length_registers * 2
        raw = raw[:need].ljust(need, b"\x00")
        return [struct.unpack(">H", raw[i : i + 2])[0] for i in range(0, len(raw), 2)]

    if isinstance(value, (int, float)):
        eng = (float(value) - offset) / scale if scale else float(value)
    else:
        eng = value

    if data_type == DataType.INT16:
        raw = struct.pack(">h", int(eng))
    elif data_type == DataType.UINT16:
        raw = struct.pack(">H", int(eng) & 0xFFFF)
    elif data_type == DataType.INT32:
        raw = struct.pack(">i", int(eng))
    elif data_type == DataType.UINT32:
        raw = struct.pack(">I", int(eng) & 0xFFFFFFFF)
    elif data_type == DataType.FLOAT32:
        raw = struct.pack(">f", float(eng))
    elif data_type == DataType.FLOAT64:
        raw = struct.pack(">d", float(eng))
    else:
        raise ValueError(f"Unsupported data type for encode: {data_type}")

    regs = [struct.unpack(">H", raw[i : i + 2])[0] for i in range(0, len(raw), 2)]
    # Inverse of decode normalization is approximate; big-endian register list is standard.
    if word_order == WordOrder.LITTLE and len(regs) > 1:
        regs = list(reversed(regs))
    if byte_order in (ByteOrder.BIG_SWAP, ByteOrder.LITTLE_SWAP):
        regs = [_swap16(r) for r in regs]
    return regs
