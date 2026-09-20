# Copyright (c) 2026 Aman Anand, M (T&I), Barauni
"""Modbus address conversion — never silently adjust by one."""

from __future__ import annotations

from app.core.enums import AddressBase, ModbusFunction, RegisterArea


def function_to_area(function: ModbusFunction) -> RegisterArea:
    if function in (ModbusFunction.READ_COILS, ModbusFunction.WRITE_COIL, ModbusFunction.WRITE_COILS):
        return RegisterArea.COIL
    if function == ModbusFunction.READ_DISCRETE:
        return RegisterArea.DISCRETE_INPUT
    if function in (
        ModbusFunction.READ_HOLDING,
        ModbusFunction.WRITE_REGISTER,
        ModbusFunction.WRITE_REGISTERS,
    ):
        return RegisterArea.HOLDING_REGISTER
    return RegisterArea.INPUT_REGISTER


def plc_display_address(area: RegisterArea, internal_zero_based: int) -> int:
    if area == RegisterArea.COIL:
        return internal_zero_based + 1
    if area == RegisterArea.DISCRETE_INPUT:
        return internal_zero_based + 10001
    if area == RegisterArea.INPUT_REGISTER:
        return internal_zero_based + 30001
    return internal_zero_based + 40001


def external_to_internal(
    address: int, address_base: AddressBase, area: RegisterArea
) -> tuple[int, int]:
    """Return (internal_zero_based, display_address)."""
    if address_base == AddressBase.ZERO:
        internal = address
        display = plc_display_address(area, internal)
        return internal, display
    # one-based / PLC style in config
    if area == RegisterArea.COIL and 1 <= address <= 9999:
        internal = address - 1
    elif area == RegisterArea.DISCRETE_INPUT and 10001 <= address <= 19999:
        internal = address - 10001
    elif area == RegisterArea.HOLDING_REGISTER and 40001 <= address <= 49999:
        internal = address - 40001
    elif area == RegisterArea.INPUT_REGISTER and 30001 <= address <= 39999:
        internal = address - 30001
    else:
        internal = address - 1 if address_base == AddressBase.ONE else address
    display = plc_display_address(area, internal)
    return internal, display
