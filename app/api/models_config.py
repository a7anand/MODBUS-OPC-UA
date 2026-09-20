# Copyright (c) 2026 Aman Anand, M (T&I), Barauni
"""API models for configuration CRUD."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from app.core.enums import AddressBase, ModbusDeviceMode


class ModbusDeviceBody(BaseModel):
    name: str = Field(min_length=1)
    mode: ModbusDeviceMode
    enabled: bool = True
    unit_id: int = Field(default=1, ge=0, le=247)
    address_base: AddressBase = AddressBase.ONE
    host: str = "127.0.0.1"
    port: int = 502
    serial_port: str = "COM1"
    baudrate: int = 9600
    bytesize: int = 8
    parity: Literal["N", "E", "O"] = "N"
    stopbits: int = 1
    response_timeout_sec: float = 1.0
    retries: int = 3


class TagDefinitionBody(BaseModel):
    name: str
    device: str
    function: int = 3
    address: int
    register_count: int = 1
    datatype: str = "uint16"
    description: str = ""
    unit_id: int = 1
    gain: float = 1.0
    offset: float = 0.0
    engineering_unit: str = ""
    opcua_node: str = ""
    poll_group: str = "default"
    enabled: bool = True
    writable: bool = False
    byte_order: str = "ABCD"
    word_order: str = "big"


class ImportTextBody(BaseModel):
    content: str = ""
    replace_existing: bool = False


class ImportCommitBody(BaseModel):
    replace_existing: bool = False


class PollGroupBody(BaseModel):
    id: str = Field(min_length=1)
    interval_ms: int = Field(default=1000, ge=50, le=3600_000)


class PollGroupIntervalBody(BaseModel):
    interval_ms: int = Field(ge=50, le=3600_000)
