# Copyright (c) 2026 Aman Anand, M (T&I), Barauni
"""Mutate gateway configuration (devices, tags) with validation."""

from __future__ import annotations

import re
from typing import Any

from app.core.config_schema import (
    GatewayDocument,
    ModbusDeviceConfig,
    PollGroupConfig,
    TagDefinition,
)
from app.core.enums import ModbusDeviceMode, OpcUaSecurityMode


class ConfigEditorError(Exception):
    pass


def list_devices(doc: GatewayDocument) -> list[dict]:
    return [d.model_dump(mode="json") for d in doc.modbus.devices]


def add_device(doc: GatewayDocument, device: ModbusDeviceConfig) -> GatewayDocument:
    names = {d.name for d in doc.modbus.devices}
    if device.name in names:
        raise ConfigEditorError(f"Device already exists: {device.name}")
    doc.modbus.devices.append(device)
    GatewayDocument.model_validate(doc.model_dump(mode="json"))
    return doc


def update_device(
    doc: GatewayDocument, name: str, device: ModbusDeviceConfig
) -> GatewayDocument:
    if device.name != name:
        names = {d.name for d in doc.modbus.devices}
        if device.name in names:
            raise ConfigEditorError(f"Device already exists: {device.name}")
        for tag in doc.tags:
            if tag.device == name:
                tag.device = device.name
    updated = False
    for i, existing in enumerate(doc.modbus.devices):
        if existing.name == name:
            doc.modbus.devices[i] = device
            updated = True
            break
    if not updated:
        raise ConfigEditorError(f"Device not found: {name}")
    return GatewayDocument.model_validate(doc.model_dump(mode="json"))


def remove_device(doc: GatewayDocument, name: str) -> GatewayDocument:
    for tag in doc.tags:
        if tag.device == name:
            raise ConfigEditorError(f"Device {name} is used by tag {tag.name}")
    remaining = [d for d in doc.modbus.devices if d.name != name]
    if not remaining:
        raise ConfigEditorError("At least one Modbus device must remain")
    doc.modbus.devices = remaining
    return doc


def list_tag_definitions(doc: GatewayDocument) -> list[dict]:
    return [t.model_dump(mode="json") for t in doc.tags]


def add_tag(doc: GatewayDocument, tag: TagDefinition) -> GatewayDocument:
    if any(t.name == tag.name for t in doc.tags):
        raise ConfigEditorError(f"Tag already exists: {tag.name}")
    device_names = {d.name for d in doc.modbus.devices}
    if tag.device not in device_names:
        raise ConfigEditorError(f"Unknown device: {tag.device}")
    doc.tags.append(tag)
    return GatewayDocument.model_validate(doc.model_dump(mode="json"))


def update_tag(doc: GatewayDocument, name: str, tag: TagDefinition) -> GatewayDocument:
    for i, existing in enumerate(doc.tags):
        if existing.name == name:
            if tag.name != name and any(t.name == tag.name for t in doc.tags):
                raise ConfigEditorError(f"Rename would duplicate tag: {tag.name}")
            doc.tags[i] = tag
            return GatewayDocument.model_validate(doc.model_dump(mode="json"))
    raise ConfigEditorError(f"Tag not found: {name}")


def remove_tag(doc: GatewayDocument, name: str) -> GatewayDocument:
    doc.tags = [t for t in doc.tags if t.name != name]
    return doc


def list_poll_groups(doc: GatewayDocument) -> list[dict]:
    return [g.model_dump(mode="json") for g in doc.poll_groups]


def update_poll_group_interval(
    doc: GatewayDocument, group_id: str, interval_ms: int
) -> GatewayDocument:
    for group in doc.poll_groups:
        if group.id == group_id:
            group.interval_ms = interval_ms
            return GatewayDocument.model_validate(doc.model_dump(mode="json"))
    raise ConfigEditorError(f"Poll group not found: {group_id}")


def add_poll_group(
    doc: GatewayDocument, group_id: str, interval_ms: int = 1000
) -> GatewayDocument:
    ids = {g.id for g in doc.poll_groups}
    if group_id in ids:
        raise ConfigEditorError(f"Poll group already exists: {group_id}")
    doc.poll_groups.append(PollGroupConfig(id=group_id, interval_ms=interval_ms))
    return GatewayDocument.model_validate(doc.model_dump(mode="json"))


def merge_imported_tags(
    doc: GatewayDocument,
    imported: list[TagDefinition],
    replace_existing: bool = False,
) -> tuple[GatewayDocument, dict]:
    """Merge tags by name. Returns doc and stats."""
    device_names = {d.name for d in doc.modbus.devices}
    added = updated = skipped = 0
    errors: list[str] = []
    by_name = {t.name: t for t in doc.tags}
    for tag in imported:
        if tag.device not in device_names:
            errors.append(f"{tag.name}: unknown device {tag.device}")
            skipped += 1
            continue
        try:
            TagDefinition.model_validate(tag.model_dump(mode="json"))
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{tag.name}: {exc}")
            skipped += 1
            continue
        if tag.name in by_name:
            if replace_existing:
                by_name[tag.name] = tag
                updated += 1
            else:
                skipped += 1
                errors.append(f"{tag.name}: already exists (use replace_existing)")
        else:
            by_name[tag.name] = tag
            added += 1
    doc.tags = list(by_name.values())
    doc = GatewayDocument.model_validate(doc.model_dump(mode="json"))
    return doc, {"added": added, "updated": updated, "skipped": skipped, "errors": errors}


_ENDPOINT_RE = re.compile(r"^opc\.tcp://([^:/]+):(\d+)(?:/)?$", re.IGNORECASE)


def parse_opcua_endpoint(endpoint: str) -> tuple[str, int]:
    m = _ENDPOINT_RE.match(endpoint.strip())
    if not m:
        raise ConfigEditorError(
            "opcua endpoint must look like opc.tcp://192.168.1.10:4841/"
        )
    return m.group(1), int(m.group(2))


def settings_to_dict(doc: GatewayDocument) -> dict[str, Any]:
    host, port = parse_opcua_endpoint(doc.opcua.server.endpoint)
    return {
        "gateway_name": doc.gateway.name,
        "gateway_mode": doc.gateway.mode,
        "web_enabled": doc.web.enabled,
        "web_host": doc.web.host,
        "web_port": doc.web.port,
        "web_remote_enabled": doc.web.remote_enabled,
        "opcua_server_enabled": doc.opcua.server.enabled,
        "opcua_host": host,
        "opcua_port": port,
        "opcua_endpoint": doc.opcua.server.endpoint,
        "opcua_application_name": doc.opcua.server.application_name,
        "opcua_security_mode": doc.opcua.server.security_mode.value,
        "logging_level": doc.logging.level,
    }


def apply_settings(doc: GatewayDocument, data: dict[str, Any]) -> tuple[GatewayDocument, bool]:
    """Apply browser-editable gateway settings. Returns (doc, web_restart_required)."""
    web_restart = (
        doc.web.host != data["web_host"].strip()
        or doc.web.port != int(data["web_port"])
    )
    opc_host = data.get("opcua_host") or data.get("opcua_host", "127.0.0.1")
    opc_port = int(data.get("opcua_port", 4841))
    if "opcua_endpoint" in data and data["opcua_endpoint"]:
        opc_host, opc_port = parse_opcua_endpoint(str(data["opcua_endpoint"]))

    doc.gateway.name = str(data["gateway_name"]).strip()
    doc.gateway.mode = str(data.get("gateway_mode", doc.gateway.mode))
    doc.web.enabled = bool(data.get("web_enabled", doc.web.enabled))
    doc.web.host = str(data["web_host"]).strip()
    doc.web.port = int(data["web_port"])
    doc.web.remote_enabled = bool(data.get("web_remote_enabled", False))
    doc.logging.level = str(data.get("logging_level", doc.logging.level))
    doc.opcua.server.enabled = bool(data.get("opcua_server_enabled", True))
    doc.opcua.server.endpoint = f"opc.tcp://{opc_host}:{opc_port}/"
    doc.opcua.server.application_name = str(
        data.get("opcua_application_name", doc.opcua.server.application_name)
    )
    mode = str(data.get("opcua_security_mode", doc.opcua.server.security_mode.value))
    try:
        doc.opcua.server.security_mode = OpcUaSecurityMode(mode)
    except ValueError as exc:
        raise ConfigEditorError(f"Invalid opcua_security_mode: {mode}") from exc
    validated = GatewayDocument.model_validate(doc.model_dump(mode="json"))
    return validated, web_restart
