# Copyright (c) 2026 Aman Anand, M (T&I), Barauni
"""Configuration models for the Modbus ↔ OPC UA gateway."""

from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, Field, field_validator, model_validator


class ModbusTransport(str, Enum):
    TCP = "tcp"
    RTU = "rtu"
    SIMULATOR = "simulator"


class RegisterArea(str, Enum):
    COIL = "coil"
    DISCRETE_INPUT = "discrete_input"
    HOLDING_REGISTER = "holding_register"
    INPUT_REGISTER = "input_register"


class DataType(str, Enum):
    BOOL = "bool"
    INT16 = "int16"
    UINT16 = "uint16"
    INT32 = "int32"
    UINT32 = "uint32"
    FLOAT32 = "float32"
    FLOAT64 = "float64"
    STRING = "string"


class ByteOrder(str, Enum):
    BIG = "big"
    LITTLE = "little"
    BIG_SWAP = "big_swap"
    LITTLE_SWAP = "little_swap"


class WordOrder(str, Enum):
    BIG = "big"
    LITTLE = "little"


class OpcUaSecurityMode(str, Enum):
    NONE = "none"
    SIGN = "sign"
    SIGN_AND_ENCRYPT = "sign_and_encrypt"


class OpcUaConfig(BaseModel):
    endpoint_host: str = "0.0.0.0"
    endpoint_port: int = 4840
    application_uri: str = "urn:aa-modbus-ua:gateway"
    product_uri: str = "urn:aa-modbus-ua:product"
    application_name: str = "AA Modbus OPC UA Gateway"
    namespace_uri: str = "urn:aa-modbus-ua:tags"
    namespace_index: int = 2
    security_mode: OpcUaSecurityMode = OpcUaSecurityMode.NONE
    certificate_path: str | None = None
    private_key_path: str | None = None


class HealthConfig(BaseModel):
    enabled: bool = True
    host: str = "127.0.0.1"
    port: int = 8091


class LoggingConfig(BaseModel):
    level: str = "INFO"
    json_logs: bool = False


class ModbusTcpConfig(BaseModel):
    host: str = "127.0.0.1"
    port: int = 502


class ModbusRtuConfig(BaseModel):
    port: str = "COM1"
    baudrate: int = 9600
    bytesize: int = 8
    parity: Literal["N", "E", "O"] = "N"
    stopbits: int = 1
    timeout_sec: float = 1.0


class ModbusConnectionConfig(BaseModel):
    id: str
    transport: ModbusTransport
    tcp: ModbusTcpConfig | None = None
    rtu: ModbusRtuConfig | None = None
    reconnect_delay_sec: float = 5.0
    request_timeout_sec: float = 1.0

    @model_validator(mode="after")
    def _transport_fields(self) -> ModbusConnectionConfig:
        if self.transport == ModbusTransport.TCP and self.tcp is None:
            self.tcp = ModbusTcpConfig()
        if self.transport == ModbusTransport.RTU and self.rtu is None:
            self.rtu = ModbusRtuConfig()
        return self


class PollGroupConfig(BaseModel):
    id: str
    interval_ms: int = Field(default=1000, ge=50)


class TagConfig(BaseModel):
    id: str
    connection_id: str
    device_name: str
    unit_id: int = Field(default=1, ge=0, le=247)
    area: RegisterArea | None = None
    address: int | None = Field(
        default=None, ge=0, description="0-based offset within the Modbus area"
    )
    modbus_address: int | None = Field(
        default=None,
        description="Optional PLC-style address (e.g. 40001); converted to offset",
    )
    data_type: DataType = DataType.UINT16
    length_registers: int = Field(default=1, ge=1, le=125)
    byte_order: ByteOrder = ByteOrder.BIG
    word_order: WordOrder = WordOrder.BIG
    scale: float = 1.0
    offset: float = 0.0
    engineering_units: str | None = None
    description: str = ""
    opcua_node_id: str | None = None
    opcua_browse_name: str | None = None
    poll_group: str = "default"
    writable: bool = False
    deadband: float = 0.0

    @field_validator("modbus_address", mode="before")
    @classmethod
    def _normalize_modbus_address(cls, v: int | None) -> int | None:
        if v is None:
            return None
        return int(v)

    @model_validator(mode="after")
    def _resolve_address(self) -> TagConfig:
        if self.modbus_address is None and (self.area is None or self.address is None):
            raise ValueError(
                f"Tag {self.id} requires modbus_address or both area and address"
            )
        if self.modbus_address is not None:
            plc = self.modbus_address
            if 1 <= plc <= 9999:
                self.area = RegisterArea.COIL
                self.address = plc - 1
            elif 10001 <= plc <= 19999:
                self.area = RegisterArea.DISCRETE_INPUT
                self.address = plc - 10001
            elif 40001 <= plc <= 49999:
                self.area = RegisterArea.HOLDING_REGISTER
                self.address = plc - 40001
            elif 30001 <= plc <= 39999:
                self.area = RegisterArea.INPUT_REGISTER
                self.address = plc - 30001
            else:
                raise ValueError(f"Unsupported PLC Modbus address: {plc}")
        if self.area is None or self.address is None:
            raise ValueError(f"Tag {self.id} missing area/address after resolution")
        if self.opcua_node_id is None:
            self.opcua_node_id = f"s={self.device_name}/{self.id}"
        if self.opcua_browse_name is None:
            self.opcua_browse_name = self.id
        if self.area in (RegisterArea.COIL, RegisterArea.DISCRETE_INPUT):
            self.data_type = DataType.BOOL
            self.length_registers = 1
        return self


class GatewayConfig(BaseModel):
    opcua: OpcUaConfig = Field(default_factory=OpcUaConfig)
    health: HealthConfig = Field(default_factory=HealthConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    poll_groups: list[PollGroupConfig] = Field(
        default_factory=lambda: [PollGroupConfig(id="default", interval_ms=1000)]
    )
    modbus_connections: list[ModbusConnectionConfig] = Field(default_factory=list)
    tags: list[TagConfig] = Field(default_factory=list)

    @model_validator(mode="after")
    def _validate_references(self) -> GatewayConfig:
        conn_ids = {c.id for c in self.modbus_connections}
        group_ids = {g.id for g in self.poll_groups}
        for tag in self.tags:
            if tag.connection_id not in conn_ids:
                raise ValueError(
                    f"Tag {tag.id} references unknown connection {tag.connection_id}"
                )
            if tag.poll_group not in group_ids:
                raise ValueError(
                    f"Tag {tag.id} references unknown poll group {tag.poll_group}"
                )
        return self


def load_config(path: Path) -> GatewayConfig:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    return GatewayConfig.model_validate(raw)
