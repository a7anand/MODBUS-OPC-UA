# Copyright (c) 2026 Aman Anand, M (T&I), Barauni
"""Mutate gateway configuration (devices, tags) with validation."""

from __future__ import annotations

from app.core.config_schema import (
    GatewayDocument,
    ModbusDeviceConfig,
    PollGroupConfig,
    TagDefinition,
)
from app.core.enums import ModbusDeviceMode


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
