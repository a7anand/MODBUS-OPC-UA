# Copyright (c) 2026 Aman Anand, M (T&I), Barauni
"""Construct Modbus devices from configuration."""

from __future__ import annotations

from app.core.config_schema import GatewayDocument, ModbusDeviceConfig
from app.core.enums import ModbusDeviceMode
from app.modbus.base import ModbusDevice, ModbusEngine
from app.modbus.rtu_client import ModbusRtuClientDevice
from app.modbus.rtu_server import ModbusRtuServerDevice
from app.modbus.simulator_device import ModbusSimulatorDevice
from app.modbus.tcp_client import ModbusTcpClientDevice
from app.modbus.tcp_server import ModbusTcpServerDevice
from app.simulator.modbus_memory import ModbusMemory


def build_modbus_engine(doc: GatewayDocument, memory: ModbusMemory | None = None) -> ModbusEngine:
    mem = memory or ModbusMemory()
    mem.seed_demo()
    engine = ModbusEngine()
    for dev_cfg in doc.modbus.devices:
        device = _create_device(dev_cfg, mem)
        engine.register(device)
    return engine


def _create_device(config: ModbusDeviceConfig, memory: ModbusMemory) -> ModbusDevice:
    mode = config.mode
    if mode == ModbusDeviceMode.TCP_CLIENT:
        return ModbusTcpClientDevice(config)
    if mode == ModbusDeviceMode.RTU_CLIENT:
        return ModbusRtuClientDevice(config)
    if mode == ModbusDeviceMode.TCP_SERVER:
        return ModbusTcpServerDevice(config, memory)
    if mode == ModbusDeviceMode.RTU_SERVER:
        return ModbusRtuServerDevice(config, memory)
    if mode == ModbusDeviceMode.SIMULATOR:
        return ModbusSimulatorDevice(config, memory)
    raise ValueError(f"Unknown modbus mode {mode}")
