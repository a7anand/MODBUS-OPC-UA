# Copyright (c) 2026 Aman Anand, M (T&I), Barauni
"""Full gateway configuration schema (YAML ↔ Pydantic)."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

from app.core.addressing import external_to_internal, function_to_area
from app.core.enums import (
    AddressBase,
    ByteLayout,
    DataType,
    MappingDirection,
    ModbusDeviceMode,
    ModbusFunction,
    OpcUaSecurityMode,
    RegisterArea,
    UserRole,
    WordOrder,
)

LOCAL_WEB_HOSTS = frozenset({"127.0.0.1", "localhost", "::1"})


class GatewayIdentityConfig(BaseModel):
    name: str = Field(min_length=1)
    mode: str = "production"

    @field_validator("name")
    @classmethod
    def _strip_name(cls, value: str) -> str:
        name = value.strip()
        if not name:
            raise ValueError("gateway.name must not be empty")
        return name


class WebConfig(BaseModel):
    enabled: bool = True
    host: str = "127.0.0.1"
    port: int = Field(default=8080, ge=1, le=65535)
    remote_enabled: bool = False

    @model_validator(mode="after")
    def _require_explicit_remote(self) -> WebConfig:
        host = self.host.strip().lower()
        if not self.remote_enabled and host not in LOCAL_WEB_HOSTS:
            raise ValueError(
                "web.host is not loopback; set web.remote_enabled: true"
            )
        return self


class LoggingConfig(BaseModel):
    level: str = "INFO"
    json_logs: bool = False


class PollGroupConfig(BaseModel):
    id: str
    interval_ms: int = Field(default=1000, ge=50)
    priority: int = Field(default=5, ge=0, le=10)


class ModbusDeviceConfig(BaseModel):
    name: str
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
    connect_timeout_sec: float = 3.0
    response_timeout_sec: float = 1.0
    retries: int = Field(default=3, ge=0)
    retry_delay_sec: float = 0.5
    reconnect_interval_sec: float = 5.0
    max_registers_per_request: int = Field(default=125, ge=1, le=125)
    keepalive: bool = True


class ModbusSection(BaseModel):
    devices: list[ModbusDeviceConfig] = Field(default_factory=list)


class OpcUaServerUser(BaseModel):
    """OPC UA username/password (distinct from REST security.users hashes)."""

    username: str
    password: str
    admin: bool = False


class OpcUaServerConfig(BaseModel):
    enabled: bool = True
    # Use 127.0.0.1 and a non-default port on Windows: 4840 is often blocked (WinError 10013).
    endpoint: str = "opc.tcp://127.0.0.1:4841"
    application_name: str = "Modbus OPC UA Gateway"
    application_uri: str = "urn:modbus-opcua-gateway:server"
    namespace_uri: str = "urn:modbus-opcua-gateway:tags"
    security_mode: OpcUaSecurityMode = OpcUaSecurityMode.NONE
    certificate_path: str | None = None
    private_key_path: str | None = None
    username_password_auth: bool = False
    server_users: list[OpcUaServerUser] = Field(default_factory=list)


class OpcUaClientSubscription(BaseModel):
    node_id: str
    tag_name: str


class OpcUaClientConfig(BaseModel):
    name: str
    endpoint: str
    enabled: bool = True
    security_mode: OpcUaSecurityMode = OpcUaSecurityMode.NONE
    username: str | None = None
    password: str | None = None
    publishing_interval_ms: int = 1000
    sampling_interval_ms: int = 500
    subscriptions: list[OpcUaClientSubscription] = Field(default_factory=list)


class OpcUaSection(BaseModel):
    server: OpcUaServerConfig = Field(default_factory=OpcUaServerConfig)
    clients: list[OpcUaClientConfig] = Field(default_factory=list)


class TagDefinition(BaseModel):
    name: str
    description: str = ""
    enabled: bool = True
    device: str
    protocol: str = "MODBUS_TCP"
    unit_id: int = Field(default=1, ge=0, le=247)
    function: ModbusFunction = ModbusFunction.READ_HOLDING
    address: int = Field(description="Address in device address_base convention")
    register_count: int = Field(default=1, ge=1, le=125)
    datatype: DataType = DataType.UINT16
    byte_order: ByteLayout = ByteLayout.ABCD
    word_order: WordOrder = WordOrder.BIG
    gain: float = 1.0
    offset: float = 0.0
    minimum: float | None = None
    maximum: float | None = None
    clamp: bool = False
    engineering_unit: str = ""
    opcua_node: str = ""
    direction: MappingDirection = MappingDirection.MB_TO_UA
    poll_interval_ms: int | None = None
    poll_group: str = "default"
    deadband: float = 0.0
    writable: bool = False
    area: RegisterArea | None = None
    address_internal: int | None = None
    address_display: int | None = None

    @model_validator(mode="after")
    def _defaults(self) -> TagDefinition:
        if not self.opcua_node:
            self.opcua_node = f"s={self.device}/{self.name}"
        return self


class MappingDefinition(BaseModel):
    id: str
    tag_name: str
    direction: MappingDirection = MappingDirection.MB_TO_UA
    enabled: bool = True
    deadband: float = 0.0


class SecurityUser(BaseModel):
    username: str
    password_hash: str = ""
    role: UserRole = UserRole.VIEWER
    enabled: bool = True


class SecurityConfig(BaseModel):
    require_auth: bool = False
    users: list[SecurityUser] = Field(default_factory=list)


class GatewayDocument(BaseModel):
    """Root configuration document."""

    gateway: GatewayIdentityConfig
    web: WebConfig = Field(default_factory=WebConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    poll_groups: list[PollGroupConfig] = Field(
        default_factory=lambda: [PollGroupConfig(id="default", interval_ms=1000)]
    )
    modbus: ModbusSection = Field(default_factory=ModbusSection)
    opcua: OpcUaSection = Field(default_factory=OpcUaSection)
    tags: list[TagDefinition] = Field(default_factory=list)
    mappings: list[MappingDefinition] = Field(default_factory=list)
    security: SecurityConfig = Field(default_factory=SecurityConfig)

    @model_validator(mode="after")
    def _cross_validate(self) -> GatewayDocument:
        device_names = {d.name for d in self.modbus.devices}
        group_ids = {g.id for g in self.poll_groups}
        tag_names: set[str] = set()
        for tag in self.tags:
            if tag.name in tag_names:
                raise ValueError(f"Duplicate tag name: {tag.name}")
            tag_names.add(tag.name)
            if tag.device not in device_names:
                raise ValueError(
                    f"Tag {tag.name} references unknown device {tag.device}"
                )
            if tag.poll_group not in group_ids:
                raise ValueError(
                    f"Tag {tag.name} references unknown poll group {tag.poll_group}"
                )
        for mapping in self.mappings:
            if mapping.tag_name not in tag_names:
                raise ValueError(
                    f"Mapping {mapping.id} references unknown tag {mapping.tag_name}"
                )
        devices = {d.name: d for d in self.modbus.devices}
        for tag in self.tags:
            dev = devices.get(tag.device)
            base = dev.address_base if dev else AddressBase.ONE
            area = tag.area or function_to_area(tag.function)
            internal, display = external_to_internal(tag.address, base, area)
            tag.area = area
            tag.address_internal = internal
            tag.address_display = display
        return self


# Backward alias for Phase 1 tests expecting GatewayConfig with gateway+web only
class GatewayConfig(GatewayDocument):
    """Alias of full document (schema v1)."""

    model_config = {"extra": "ignore"}
