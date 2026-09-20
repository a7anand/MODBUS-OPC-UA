# Copyright (c) 2026 Aman Anand, M (T&I), Barauni
"""Modbus TCP simulator service wrapper."""

from __future__ import annotations

from app.core.config_schema import ModbusDeviceConfig
from app.core.enums import ModbusDeviceMode
from app.modbus.simulator_device import ModbusSimulatorDevice
from app.simulator.modbus_memory import ModbusMemory


def create_default_simulator(name: str = "SIM_PLC") -> ModbusSimulatorDevice:
    cfg = ModbusDeviceConfig(name=name, mode=ModbusDeviceMode.SIMULATOR)
    return ModbusSimulatorDevice(cfg, ModbusMemory())
