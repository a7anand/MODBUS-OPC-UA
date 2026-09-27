# Copyright (c) 2026 Aman Anand, M (T&I), Barauni
"""Configuration CRUD routes (devices, tags, import)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from app.api.models_config import (
    GatewaySettingsBody,
    ImportCommitBody,
    ImportTextBody,
    ModbusDeviceBody,
    PollGroupBody,
    PollGroupIntervalBody,
    RegisterBitExpandBody,
    RegisterBitPreviewBody,
    TagDefinitionBody,
    YamlDocumentBody,
)
from app.core.enums import RegisterArea
from app.core.register_bit_decode import (
    build_bool_tag,
    parse_four_x_address,
    preview_register_bits,
)
from app.core.config_editor import (
    ConfigEditorError,
    add_device,
    add_poll_group,
    add_tag,
    apply_settings,
    list_devices,
    list_poll_groups,
    list_tag_definitions,
    merge_imported_tags,
    remove_device,
    remove_tag,
    settings_to_dict,
    update_device,
    update_poll_group_interval,
    update_tag,
)
from app.core.config_manager import ConfigManager
from app.core.config_schema import GatewayDocument, ModbusDeviceConfig, TagDefinition
from app.core.enums import ByteLayout, DataType, MappingDirection, ModbusFunction, WordOrder
from app.core.gateway import Gateway
from app.core.mapping_feedback import validate_mappings
from app.core.import_export import (
    export_tags_csv,
    import_tags_csv,
    import_tags_excel,
    rows_to_tag_definitions,
)

_pending_import: dict[str, Any] = {"rows": []}


def _tag_from_body(body: TagDefinitionBody) -> TagDefinition:
    return TagDefinition(
        name=body.name.strip(),
        description=body.description,
        device=body.device.strip(),
        unit_id=body.unit_id,
        function=ModbusFunction(body.function),
        address=body.address,
        register_count=body.register_count,
        datatype=DataType(body.datatype.lower()),
        byte_order=ByteLayout(body.byte_order.upper()),
        word_order=WordOrder(body.word_order.lower()),
        gain=body.gain,
        offset=body.offset,
        engineering_unit=body.engineering_unit,
        opcua_node=body.opcua_node or f"s={body.device}/{body.name}",
        poll_group=body.poll_group,
        enabled=body.enabled,
        writable=body.writable,
        bit_index=body.bit_index,
    )


def register_config_routes(
    app_router: APIRouter,
    gateway: Gateway,
    session_dep: Any,
) -> None:
    """Browser config API: devices, tags (incl. edit), poll groups, CSV/Excel import."""
    @app_router.get("/settings")
    async def get_gateway_settings() -> dict[str, Any]:
        if not gateway.doc:
            return {}
        return settings_to_dict(gateway.doc)

    @app_router.put("/settings")
    async def put_gateway_settings(
        body: GatewaySettingsBody, user: str = Depends(session_dep)
    ) -> dict[str, Any]:
        if gateway.authz and not gateway.authz.can_write(user):
            raise HTTPException(403, "Forbidden")
        if not gateway.doc:
            raise HTTPException(503, "Gateway not loaded")
        try:
            doc, web_restart = apply_settings(
                gateway.doc.model_copy(deep=True), body.model_dump()
            )
        except ConfigEditorError as exc:
            raise HTTPException(400, str(exc)) from exc
        await gateway.persist_document(doc, user=user, description="gateway settings")
        msg = "Settings saved and engines reloaded."
        if web_restart:
            msg += (
                " Web listen address changed — restart the gateway process "
                "(or Windows service) to apply the new HTTP port/host."
            )
        return {"ok": True, "message": msg, "web_restart_required": web_restart}

    @app_router.post("/yaml/validate")
    async def validate_gateway_yaml(body: YamlDocumentBody) -> dict[str, Any]:
        try:
            data = yaml.safe_load(body.content)
            if not isinstance(data, dict):
                raise HTTPException(400, "YAML root must be a mapping")
            doc = ConfigManager().validate(data)
            map_errs = validate_mappings(doc)
            if map_errs:
                return {"valid": False, "error": "; ".join(map_errs)}
            return {"valid": True}
        except HTTPException:
            raise
        except Exception as exc:  # noqa: BLE001
            return {"valid": False, "error": str(exc)}

    @app_router.get("/yaml")
    async def get_gateway_yaml() -> dict[str, str]:
        path = gateway.config_path
        if not path.is_file():
            raise HTTPException(404, "Config file not found")
        return {"path": str(path), "content": path.read_text(encoding="utf-8")}

    @app_router.put("/yaml")
    async def put_gateway_yaml(
        body: YamlDocumentBody, user: str = Depends(session_dep)
    ) -> dict[str, Any]:
        if gateway.authz and not gateway.authz.can_write(user):
            raise HTTPException(403, "Forbidden")
        try:
            data = yaml.safe_load(body.content)
            if not isinstance(data, dict):
                raise HTTPException(400, "YAML root must be a mapping")
            doc = ConfigManager().validate(data)
        except HTTPException:
            raise
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(400, str(exc)) from exc
        old_web = (
            (gateway.doc.web.host, gateway.doc.web.port) if gateway.doc else (None, None)
        )
        gateway.config_manager.backup_active(
            gateway.config_path, user=user, description="pre-yaml-edit backup"
        )
        gateway.config_path.write_text(
            yaml.safe_dump(doc.model_dump(mode="json"), sort_keys=False),
            encoding="utf-8",
        )
        await gateway.reload_config()
        web_restart = gateway.doc and (
            gateway.doc.web.host != old_web[0] or gateway.doc.web.port != old_web[1]
        )
        gateway.audit.record(user, "config_yaml_edit", str(gateway.config_path))
        msg = "YAML saved and reloaded."
        if web_restart:
            msg += " Restart the gateway for web host/port changes."
        return {"ok": True, "message": msg, "web_restart_required": bool(web_restart)}

    @app_router.get("/modbus/devices")
    async def get_modbus_devices_config() -> list[dict[str, Any]]:
        if not gateway.doc:
            return []
        return list_devices(gateway.doc)

    @app_router.post("/modbus/devices")
    async def post_modbus_device(
        body: ModbusDeviceBody, user: str = Depends(session_dep)
    ) -> dict[str, Any]:
        if gateway.authz and not gateway.authz.can_write(user):
            raise HTTPException(403, "Forbidden")
        if not gateway.doc:
            raise HTTPException(503, "Gateway not loaded")
        device = ModbusDeviceConfig.model_validate(body.model_dump())
        try:
            doc = add_device(gateway.doc.model_copy(deep=True), device)
        except ConfigEditorError as exc:
            raise HTTPException(400, str(exc)) from exc
        await gateway.persist_document(doc, user=user, description=f"add device {body.name}")
        return {"ok": True, "device": body.name}

    @app_router.put("/modbus/devices/{device_name}")
    async def put_modbus_device(
        device_name: str, body: ModbusDeviceBody, user: str = Depends(session_dep)
    ) -> dict[str, Any]:
        if gateway.authz and not gateway.authz.can_write(user):
            raise HTTPException(403, "Forbidden")
        if not gateway.doc:
            raise HTTPException(503, "Gateway not loaded")
        payload = body.model_dump()
        payload["name"] = body.name.strip() or device_name
        device = ModbusDeviceConfig.model_validate(payload)
        try:
            doc = update_device(gateway.doc.model_copy(deep=True), device_name, device)
        except ConfigEditorError as exc:
            raise HTTPException(400, str(exc)) from exc
        await gateway.persist_document(
            doc, user=user, description=f"update device {device_name}"
        )
        return {"ok": True, "device": device.name}

    @app_router.delete("/modbus/devices/{device_name}")
    async def delete_modbus_device(
        device_name: str, user: str = Depends(session_dep)
    ) -> dict[str, Any]:
        if gateway.authz and not gateway.authz.can_write(user):
            raise HTTPException(403, "Forbidden")
        if not gateway.doc:
            raise HTTPException(503, "Gateway not loaded")
        try:
            doc = remove_device(gateway.doc.model_copy(deep=True), device_name)
        except ConfigEditorError as exc:
            raise HTTPException(400, str(exc)) from exc
        await gateway.persist_document(doc, user=user, description=f"remove device {device_name}")
        return {"ok": True}

    def _resolve_holding_address(
        body: RegisterBitPreviewBody | RegisterBitExpandBody,
    ) -> int:
        if body.four_x:
            plc, _bit = parse_four_x_address(body.four_x)
            return plc
        if body.address is None:
            raise HTTPException(400, "address or four_x required")
        return body.address

    @app_router.post("/tags/register-bits/preview")
    async def preview_holding_register_bits(
        body: RegisterBitPreviewBody,
    ) -> dict[str, Any]:
        if not gateway.modbus_diag:
            raise HTTPException(503, "Gateway not ready")
        plc = _resolve_holding_address(body)
        dev = gateway.doc and next(
            (d for d in gateway.doc.modbus.devices if d.name == body.device), None
        )
        if dev is None:
            raise HTTPException(404, "Device not found")
        from app.core.addressing import external_to_internal, function_to_area
        from app.core.enums import ModbusFunction

        area = RegisterArea.HOLDING_REGISTER
        internal, display = external_to_internal(
            plc, dev.address_base, function_to_area(ModbusFunction.READ_HOLDING)
        )
        result = await gateway.modbus_diag.read(
            body.device, body.unit_id, area, internal, 1
        )
        if not result.get("ok"):
            raise HTTPException(502, result.get("error") or "Modbus read failed")
        regs = result.get("registers") or [0]
        word = regs[0]
        four_x = display - 40001 if display >= 40001 else internal
        return {
            "device": body.device,
            "plc_address": display,
            "four_x": f"4X:{four_x}",
            "register_value": word,
            "hex": f"{word:04X}",
            "bits": preview_register_bits(word),
        }

    @app_router.post("/tags/register-bits/expand")
    async def expand_register_bits_to_tags(
        body: RegisterBitExpandBody, user: str = Depends(session_dep)
    ) -> dict[str, Any]:
        if gateway.authz and not gateway.authz.can_write(user):
            raise HTTPException(403, "Forbidden")
        if not gateway.doc:
            raise HTTPException(503, "Gateway not loaded")
        plc = _resolve_holding_address(body)
        doc = gateway.doc.model_copy(deep=True)
        created: list[str] = []
        for item in body.bits:
            tag_name = item.name.strip()
            if body.name_prefix and not tag_name.startswith(body.name_prefix):
                tag_name = f"{body.name_prefix}{tag_name}"
            tag = build_bool_tag(
                tag_name,
                body.device,
                plc,
                item.bit,
                description=item.description,
                writable=item.writable,
                poll_group=body.poll_group,
            )
            try:
                doc = add_tag(doc, tag)
            except ConfigEditorError as exc:
                raise HTTPException(400, str(exc)) from exc
            created.append(tag.name)
        await gateway.persist_document(
            doc, user=user, description=f"register bit expand {body.four_x or plc}"
        )
        return {"ok": True, "created": created, "count": len(created)}

    @app_router.get("/tags/definitions")
    async def get_tag_definitions() -> list[dict[str, Any]]:
        if not gateway.doc:
            return []
        return list_tag_definitions(gateway.doc)

    @app_router.post("/tags/definitions")
    async def post_tag_definition(
        body: TagDefinitionBody, user: str = Depends(session_dep)
    ) -> dict[str, Any]:
        if gateway.authz and not gateway.authz.can_write(user):
            raise HTTPException(403, "Forbidden")
        if not gateway.doc:
            raise HTTPException(503, "Gateway not loaded")
        tag = _tag_from_body(body)
        try:
            doc = add_tag(gateway.doc.model_copy(deep=True), tag)
        except ConfigEditorError as exc:
            raise HTTPException(400, str(exc)) from exc
        await gateway.persist_document(doc, user=user, description=f"add tag {tag.name}")
        return {"ok": True, "tag": tag.name}

    @app_router.put("/tags/definitions/{tag_name}")
    async def put_tag_definition(
        tag_name: str, body: TagDefinitionBody, user: str = Depends(session_dep)
    ) -> dict[str, Any]:
        if gateway.authz and not gateway.authz.can_write(user):
            raise HTTPException(403, "Forbidden")
        if not gateway.doc:
            raise HTTPException(503, "Gateway not loaded")
        tag = _tag_from_body(body)
        try:
            doc = update_tag(gateway.doc.model_copy(deep=True), tag_name, tag)
        except ConfigEditorError as exc:
            raise HTTPException(400, str(exc)) from exc
        await gateway.persist_document(
            doc, user=user, description=f"update tag {tag_name} -> {tag.name}"
        )
        return {"ok": True, "tag": tag.name}

    @app_router.delete("/tags/definitions/{tag_name}")
    async def delete_tag_definition(
        tag_name: str, user: str = Depends(session_dep)
    ) -> dict[str, Any]:
        if gateway.authz and not gateway.authz.can_write(user):
            raise HTTPException(403, "Forbidden")
        if not gateway.doc:
            raise HTTPException(503, "Gateway not loaded")
        doc = remove_tag(gateway.doc.model_copy(deep=True), tag_name)
        await gateway.persist_document(doc, user=user, description=f"remove tag {tag_name}")
        return {"ok": True}

    @app_router.get("/poll-groups")
    async def get_poll_groups() -> list[dict[str, Any]]:
        if not gateway.doc:
            return []
        return list_poll_groups(gateway.doc)

    @app_router.post("/poll-groups")
    async def post_poll_group(
        body: PollGroupBody, user: str = Depends(session_dep)
    ) -> dict[str, Any]:
        if gateway.authz and not gateway.authz.can_write(user):
            raise HTTPException(403, "Forbidden")
        if not gateway.doc:
            raise HTTPException(503, "Gateway not loaded")
        try:
            doc = add_poll_group(
                gateway.doc.model_copy(deep=True), body.id, body.interval_ms
            )
        except ConfigEditorError as exc:
            raise HTTPException(400, str(exc)) from exc
        await gateway.persist_document(
            doc, user=user, description=f"add poll group {body.id}"
        )
        return {"ok": True}

    @app_router.put("/poll-groups/{group_id}")
    async def put_poll_group_interval(
        group_id: str, body: PollGroupIntervalBody, user: str = Depends(session_dep)
    ) -> dict[str, Any]:
        if gateway.authz and not gateway.authz.can_write(user):
            raise HTTPException(403, "Forbidden")
        if not gateway.doc:
            raise HTTPException(503, "Gateway not loaded")
        try:
            doc = update_poll_group_interval(
                gateway.doc.model_copy(deep=True), group_id, body.interval_ms
            )
        except ConfigEditorError as exc:
            raise HTTPException(400, str(exc)) from exc
        await gateway.persist_document(
            doc, user=user, description=f"poll group {group_id} -> {body.interval_ms}ms"
        )
        return {"ok": True}

    @app_router.get("/tags/export/csv")
    async def download_tags_csv() -> dict[str, str]:
        if not gateway.doc:
            return {"content": ""}
        return {"content": export_tags_csv(gateway.doc.tags)}

    @app_router.post("/tags/import/preview-json")
    async def import_preview_json(body: dict[str, Any]) -> dict[str, Any]:
        raw = body.get("tags") if isinstance(body.get("tags"), list) else body
        if not isinstance(raw, list):
            raise HTTPException(400, "Expected JSON array or {tags: [...]}")
        tags = [TagDefinition.model_validate(t) for t in raw]
        _pending_import["rows"] = [t.model_dump(mode="json") for t in tags]
        return {"row_count": len(tags), "valid_tags": len(tags), "errors": [], "preview": raw[:25]}

    @app_router.post("/tags/import/preview-yaml")
    async def import_preview_yaml(body: ImportTextBody) -> dict[str, Any]:
        data = yaml.safe_load(body.content) or {}
        raw = data.get("tags", data if isinstance(data, list) else [])
        tags = [TagDefinition.model_validate(t) for t in raw]
        _pending_import["rows"] = [t.model_dump(mode="json") for t in tags]
        return {"row_count": len(tags), "valid_tags": len(tags), "errors": [], "preview": raw[:25]}

    @app_router.post("/tags/import/preview")
    async def import_preview(body: ImportTextBody) -> dict[str, Any]:
        rows = import_tags_csv(body.content)
        tags, errors = rows_to_tag_definitions(rows)
        _pending_import["rows"] = [t.model_dump(mode="json") for t in tags]
        return {
            "row_count": len(rows),
            "valid_tags": len(tags),
            "errors": errors,
            "preview": rows[:25],
        }

    @app_router.post("/tags/import/preview-file")
    async def import_preview_file(file: UploadFile = File(...)) -> dict[str, Any]:
        raw = await file.read()
        name = (file.filename or "").lower()
        if name.endswith(".xlsx") or name.endswith(".xlsm"):
            try:
                rows = import_tags_excel(raw)
            except ImportError as exc:
                raise HTTPException(501, str(exc)) from exc
        else:
            text = raw.decode("utf-8-sig", errors="replace")
            rows = import_tags_csv(text)
        tags, errors = rows_to_tag_definitions(rows)
        _pending_import["rows"] = [t.model_dump(mode="json") for t in tags]
        Path("imports").mkdir(exist_ok=True)
        dest = Path("imports") / (file.filename or "upload.csv")
        dest.write_bytes(raw)
        return {
            "file": str(dest),
            "row_count": len(rows),
            "valid_tags": len(tags),
            "errors": errors,
            "preview": rows[:25],
        }

    @app_router.post("/tags/import/commit")
    async def import_commit(
        body: ImportCommitBody, user: str = Depends(session_dep)
    ) -> dict[str, Any]:
        if gateway.authz and not gateway.authz.can_write(user):
            raise HTTPException(403, "Forbidden")
        if not gateway.doc:
            raise HTTPException(503, "Gateway not loaded")
        pending = _pending_import.get("rows") or []
        if not pending:
            raise HTTPException(400, "No import preview — upload or preview first")
        tags = [TagDefinition.model_validate(t) for t in pending]
        doc = gateway.doc.model_copy(deep=True)
        doc, stats = merge_imported_tags(doc, tags, replace_existing=body.replace_existing)
        await gateway.persist_document(
            doc, user=user, description=f"import {len(tags)} tags"
        )
        _pending_import["rows"] = []
        return {"ok": True, "stats": stats}
