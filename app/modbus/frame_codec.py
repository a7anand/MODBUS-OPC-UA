# Copyright (c) 2026 Aman Anand, M (T&I), Barauni
"""Synthetic Modbus PDU hex for diagnostics (RTU-style PDU, no TCP MBAP header)."""

from __future__ import annotations


def _hex_bytes(data: bytes) -> str:
    return " ".join(f"{b:02X}" for b in data)


def read_request_pdu(unit_id: int, function: int, address: int, count: int) -> str:
    """Build expected read request PDU (unit + function + addr + quantity)."""
    pdu = bytes(
        [
            unit_id & 0xFF,
            function & 0xFF,
            (address >> 8) & 0xFF,
            address & 0xFF,
            (count >> 8) & 0xFF,
            count & 0xFF,
        ]
    )
    return _hex_bytes(pdu)


def read_response_pdu(unit_id: int, function: int, registers: list[int]) -> str:
    """Build response PDU for successful register read."""
    body: list[int] = []
    for reg in registers:
        body.append((reg >> 8) & 0xFF)
        body.append(reg & 0xFF)
    pdu = bytes([unit_id & 0xFF, function & 0xFF, len(body) & 0xFF, *body])
    return _hex_bytes(pdu)


def read_exchange_hex(
    unit_id: int,
    function: int,
    address: int,
    count: int,
    registers: list[int] | None,
    ok: bool,
) -> tuple[str, str]:
    """Return (tx_hex, rx_hex) for a read transaction."""
    tx = read_request_pdu(unit_id, function, address, count)
    if ok and registers is not None:
        rx = read_response_pdu(unit_id, function, registers)
    elif ok:
        rx = ""
    else:
        rx = f"{unit_id:02X} {function | 0x80:02X} …"
    return tx, rx
