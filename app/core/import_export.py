# Copyright (c) 2026 Aman Anand, M (T&I), Barauni
"""Tag import/export CSV, JSON, YAML, Excel."""

from __future__ import annotations

import csv
import json
from io import BytesIO, StringIO
from pathlib import Path
from typing import Any

import yaml

from app.core.config_schema import TagDefinition
from app.core.enums import (
    ByteLayout,
    DataType,
    MappingDirection,
    ModbusFunction,
    WordOrder,
)

CSV_FIELDS = [
    "TagName",
    "Description",
    "Device",
    "Protocol",
    "UnitID",
    "Function",
    "Address",
    "RegisterCount",
    "Datatype",
    "ByteOrder",
    "WordOrder",
    "Gain",
    "Offset",
    "EngineeringUnit",
    "OPCUANode",
    "Direction",
    "PollInterval",
    "Enabled",
]

# Aliases for spreadsheet headers (case-insensitive)
_HEADER_ALIASES = {
    "tagname": "TagName",
    "tag": "TagName",
    "name": "TagName",
    "device": "Device",
    "unitid": "UnitID",
    "unit_id": "UnitID",
    "function": "Function",
    "address": "Address",
    "modbus_address": "Address",
    "registercount": "RegisterCount",
    "datatype": "Datatype",
    "data_type": "Datatype",
    "byteorder": "ByteOrder",
    "wordorder": "WordOrder",
    "gain": "Gain",
    "scale": "Gain",
    "offset": "Offset",
    "engineeringunit": "EngineeringUnit",
    "opcuanode": "OPCUANode",
    "opcua_node": "OPCUANode",
    "direction": "Direction",
    "pollinterval": "PollInterval",
    "poll_group": "PollInterval",
    "enabled": "Enabled",
    "description": "Description",
    "protocol": "Protocol",
}


def _normalize_row(row: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, value in row.items():
        if key is None:
            continue
        k = str(key).strip()
        canon = _HEADER_ALIASES.get(k.lower(), k)
        out[canon] = value
    return out


def _parse_bool(value: Any, default: bool = True) -> bool:
    if value is None or value == "":
        return default
    if isinstance(value, bool):
        return value
    s = str(value).strip().lower()
    return s in ("1", "true", "yes", "y", "on")


def row_to_tag_definition(row: dict[str, Any]) -> TagDefinition:
    row = _normalize_row(row)
    name = str(row.get("TagName", "")).strip()
    if not name:
        raise ValueError("TagName is required")
    device = str(row.get("Device", "")).strip()
    if not device:
        raise ValueError(f"Device is required for tag {name}")
    func_raw = row.get("Function", 3)
    function = ModbusFunction(int(func_raw))
    datatype = DataType(str(row.get("Datatype", "uint16")).strip().lower())
    byte_order = ByteLayout(str(row.get("ByteOrder", "ABCD")).strip().upper())
    word_order = WordOrder(str(row.get("WordOrder", "big")).strip().lower())
    direction = MappingDirection(
        str(row.get("Direction", "mb_to_ua")).strip().lower()
    )
    poll_ms = row.get("PollInterval")
    poll_group = "default"
    if poll_ms not in (None, ""):
        try:
            ms = int(poll_ms)
            poll_group = "fast" if ms <= 500 else "default"
        except (TypeError, ValueError):
            poll_group = str(poll_ms)
    return TagDefinition(
        name=name,
        description=str(row.get("Description", "") or ""),
        enabled=_parse_bool(row.get("Enabled"), True),
        device=device,
        protocol=str(row.get("Protocol", "MODBUS_TCP") or "MODBUS_TCP"),
        unit_id=int(row.get("UnitID", 1) or 1),
        function=function,
        address=int(row.get("Address", 0)),
        register_count=int(row.get("RegisterCount", 1) or 1),
        datatype=datatype,
        byte_order=byte_order,
        word_order=word_order,
        gain=float(row.get("Gain", 1) or 1),
        offset=float(row.get("Offset", 0) or 0),
        engineering_unit=str(row.get("EngineeringUnit", "") or ""),
        opcua_node=str(row.get("OPCUANode", "") or ""),
        direction=direction,
        poll_group=poll_group,
    )


def rows_to_tag_definitions(rows: list[dict[str, Any]]) -> tuple[list[TagDefinition], list[str]]:
    tags: list[TagDefinition] = []
    errors: list[str] = []
    for i, row in enumerate(rows, start=2):
        try:
            tags.append(row_to_tag_definition(row))
        except Exception as exc:  # noqa: BLE001
            errors.append(f"Row {i}: {exc}")
    return tags, errors


def export_tags_csv(tags: list[TagDefinition]) -> str:
    buf = StringIO()
    writer = csv.DictWriter(buf, fieldnames=CSV_FIELDS)
    writer.writeheader()
    for t in tags:
        writer.writerow(
            {
                "TagName": t.name,
                "Description": t.description,
                "Device": t.device,
                "Protocol": t.protocol,
                "UnitID": t.unit_id,
                "Function": t.function.value,
                "Address": t.address,
                "RegisterCount": t.register_count,
                "Datatype": t.datatype.value,
                "ByteOrder": t.byte_order.value,
                "WordOrder": t.word_order.value,
                "Gain": t.gain,
                "Offset": t.offset,
                "EngineeringUnit": t.engineering_unit,
                "OPCUANode": t.opcua_node,
                "Direction": t.direction.value,
                "PollInterval": t.poll_interval_ms or "",
                "Enabled": t.enabled,
            }
        )
    return buf.getvalue()


def export_tags_json(tags: list[TagDefinition]) -> str:
    return json.dumps([t.model_dump(mode="json") for t in tags], indent=2)


def export_tags_yaml(tags: list[TagDefinition]) -> str:
    return yaml.safe_dump([t.model_dump(mode="json") for t in tags])


def import_tags_csv(content: str) -> list[dict[str, Any]]:
    reader = csv.DictReader(StringIO(content))
    return [_normalize_row(dict(r)) for r in reader]


def import_tags_excel(data: bytes) -> list[dict[str, Any]]:
    try:
        import openpyxl
    except ImportError as exc:
        raise ImportError(
            "Excel import requires openpyxl: pip install openpyxl"
        ) from exc
    wb = openpyxl.load_workbook(BytesIO(data), read_only=True, data_only=True)
    sheet = wb.active
    rows_iter = sheet.iter_rows(values_only=True)
    header = next(rows_iter, None)
    if not header:
        return []
    keys = [str(h).strip() if h is not None else "" for h in header]
    out: list[dict[str, Any]] = []
    for row in rows_iter:
        if not any(row):
            continue
        item = {keys[i]: row[i] for i in range(len(keys)) if keys[i]}
        out.append(_normalize_row(item))
    return out


def write_export(path: Path, tags: list[TagDefinition], fmt: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fmt == "csv":
        path.write_text(export_tags_csv(tags), encoding="utf-8")
    elif fmt == "json":
        path.write_text(export_tags_json(tags), encoding="utf-8")
    else:
        path.write_text(export_tags_yaml(tags), encoding="utf-8")
