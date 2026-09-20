# Copyright (c) 2026 Aman Anand, M (T&I), Barauni
"""FastAPI application."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, FastAPI, Header, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from app.core.config_manager import ConfigManager
from app.core.enums import RegisterArea
from app.core.gateway import Gateway
from app.api.routes.config_api import register_config_routes
from app.api.websocket import router as ws_router

from app.utils.runtime_paths import app_root, bundle_dir, is_frozen

WEB_DIR = Path(__file__).resolve().parents[1] / "web"
if not (WEB_DIR / "templates").is_dir():
    WEB_DIR = bundle_dir() / "app" / "web"
PROJECT_ROOT = app_root() if is_frozen() else Path(__file__).resolve().parents[2]


class TagWriteBody(BaseModel):
    value: Any


class ModbusReadBody(BaseModel):
    device: str
    unit_id: int = 1
    area: str = "holding_register"
    address: int = 0
    count: int = 1


class ModbusWriteBody(ModbusReadBody):
    values: list[int]


class OpcUaReadBody(BaseModel):
    client: str | None = None
    node_id: str


class OpcUaWriteBody(OpcUaReadBody):
    value: Any


class LoginBody(BaseModel):
    username: str = ""
    password: str = ""


def create_app(gateway: Gateway) -> FastAPI:
    app = FastAPI(title="Modbus OPC UA Gateway API", version="0.1.0")
    templates = Jinja2Templates(directory=str(WEB_DIR / "templates"))
    static_path = WEB_DIR / "static"
    if static_path.is_dir():
        app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

    def _session(authorization: str | None = Header(default=None)) -> str:
        token = None
        if authorization and authorization.startswith("Bearer "):
            token = authorization[7:]
        sess = gateway.auth.validate(token) if gateway.auth else None
        if gateway.doc and gateway.doc.security.require_auth and sess is None:
            raise HTTPException(status_code=401, detail="Unauthorized")
        return sess.username if sess else "anonymous"

    @app.get("/", response_class=HTMLResponse)
    async def dashboard(request: Request) -> HTMLResponse:
        return templates.TemplateResponse(
            request,
            "dashboard.html",
            {"gateway": gateway.doc.gateway.name if gateway.doc else ""},
        )

    @app.get("/tags", response_class=HTMLResponse)
    async def page_tags(request: Request) -> HTMLResponse:
        return templates.TemplateResponse(request, "tags.html", {})

    @app.get("/devices", response_class=HTMLResponse)
    async def page_devices(request: Request) -> HTMLResponse:
        return templates.TemplateResponse(request, "devices.html", {})

    @app.get("/import", response_class=HTMLResponse)
    async def page_import(request: Request) -> HTMLResponse:
        return templates.TemplateResponse(request, "import.html", {})

    @app.get("/examples/tags_import_template.csv")
    async def tags_template_csv() -> FileResponse:
        path = PROJECT_ROOT / "examples" / "tags_import_template.csv"
        return FileResponse(path, filename="tags_import_template.csv", media_type="text/csv")

    @app.get("/events", response_class=HTMLResponse)
    async def page_events(request: Request) -> HTMLResponse:
        return templates.TemplateResponse(request, "events.html", {})

    @app.get("/diagnostics", response_class=HTMLResponse)
    async def page_diagnostics(request: Request) -> HTMLResponse:
        return templates.TemplateResponse(request, "diagnostics.html", {})

    @app.get("/trends", response_class=HTMLResponse)
    async def page_trends(request: Request) -> HTMLResponse:
        return templates.TemplateResponse(request, "trends.html", {})

    @app.get("/traffic", response_class=HTMLResponse)
    async def page_traffic(request: Request) -> HTMLResponse:
        return templates.TemplateResponse(request, "traffic.html", {})

    @app.get("/polling", response_class=HTMLResponse)
    async def page_polling(request: Request) -> HTMLResponse:
        return templates.TemplateResponse(request, "polling.html", {})

    @app.get("/history", response_class=HTMLResponse)
    async def page_history(request: Request) -> HTMLResponse:
        return templates.TemplateResponse(request, "history.html", {})

    @app.get("/api/status")
    async def api_status() -> dict[str, Any]:
        return gateway.status()

    @app.get("/api/tags")
    async def api_tags() -> list[dict[str, Any]]:
        return gateway.tags.snapshot()

    @app.get("/api/tags/{tag_name}")
    async def api_tag(tag_name: str) -> dict[str, Any]:
        rec = gateway.tags.get(tag_name)
        if not rec:
            raise HTTPException(404, "Tag not found")
        return rec.to_dict()

    @app.put("/api/tags/{tag_name}")
    async def api_tag_write(
        tag_name: str, body: TagWriteBody, user: str = Depends(_session)
    ) -> dict[str, Any]:
        ok = await gateway.write_tag(tag_name, body.value, user)
        if not ok:
            raise HTTPException(400, "Write failed")
        return {"ok": True}

    @app.get("/api/devices")
    async def api_devices() -> list[dict[str, Any]]:
        return gateway.modbus.status() if gateway.modbus else []

    @app.get("/api/modbus/status")
    async def modbus_status() -> list[dict[str, Any]]:
        return gateway.modbus.status() if gateway.modbus else []

    @app.get("/api/opcua/status")
    async def opcua_status() -> dict[str, Any]:
        server = gateway.opcua_server
        return {
            "server_enabled": gateway.doc.opcua.server.enabled if gateway.doc else False,
            "server_running": bool(server and server.started),
            "server_endpoint": server.bound_endpoint if server else None,
            "clients": [c.config.name for c in gateway.opcua_clients],
        }

    @app.get("/api/events")
    async def api_events() -> list[dict[str, Any]]:
        return gateway.events.list_events()

    @app.get("/api/config")
    async def api_config() -> dict[str, Any]:
        if not gateway.doc:
            return {}
        return gateway.doc.model_dump(mode="json")

    @app.post("/api/config/validate")
    async def api_validate_config(payload: dict[str, Any]) -> dict[str, Any]:
        try:
            ConfigManager().validate(payload)
            return {"valid": True}
        except Exception as exc:  # noqa: BLE001
            return {"valid": False, "error": str(exc)}

    @app.post("/api/config/apply")
    async def api_apply_config(
        payload: dict[str, Any], user: str = Depends(_session)
    ) -> dict[str, Any]:
        if gateway.authz and not gateway.authz.can_write(user):
            raise HTTPException(403, "Forbidden")
        doc = ConfigManager().validate(payload)
        gateway.config_manager.apply_with_store(
            doc, gateway.config_path, gateway.store, user=user
        )
        gateway.audit.record(user, "config_apply", str(gateway.config_path))
        await gateway.reload_config()
        return {"ok": True, "message": "Configuration applied and engines reloaded"}

    @app.get("/api/config/revisions")
    async def api_config_revisions() -> list[dict[str, Any]]:
        return gateway.store.list_config_revisions()

    @app.get("/api/config/revisions/compare")
    async def api_config_revisions_compare(
        left: int, right: int
    ) -> dict[str, Any]:
        a = gateway.store.get_config_revision(left)
        b = gateway.store.get_config_revision(right)
        if a is None or b is None:
            raise HTTPException(404, "Revision not found")
        import difflib

        diff = list(
            difflib.unified_diff(
                a.splitlines(),
                b.splitlines(),
                fromfile=f"rev-{left}",
                tofile=f"rev-{right}",
                lineterm="",
            )
        )
        return {"left": left, "right": right, "diff": diff, "identical": a == b}

    @app.post("/api/config/reload")
    async def api_config_reload(user: str = Depends(_session)) -> dict[str, Any]:
        if gateway.authz and not gateway.authz.can_write(user):
            raise HTTPException(403, "Forbidden")
        await gateway.reload_config()
        return {"ok": True}

    @app.get("/api/backups")
    async def api_backups() -> list[dict[str, Any]]:
        return gateway.backups.list_backups()

    @app.post("/api/backups")
    async def api_create_backup(user: str = Depends(_session)) -> dict[str, Any]:
        path = gateway.config_manager.backup_active(gateway.config_path, user=user)
        return {"file": str(path)}

    @app.post("/api/restore")
    async def api_restore(backup_path: str, user: str = Depends(_session)) -> dict[str, Any]:
        gateway.backups.restore(Path(backup_path), gateway.config_path)
        gateway.audit.record(user, "config_restore", backup_path)
        return {"ok": True}

    @app.get("/api/opcua/browse")
    async def api_opcua_browse() -> list[dict[str, Any]]:
        if gateway.opcua_server:
            return await gateway.opcua_server.browse()
        return []

    @app.post("/api/modbus/read")
    async def api_modbus_read(body: ModbusReadBody) -> dict[str, Any]:
        if not gateway.modbus_diag:
            raise HTTPException(503, "Not ready")
        area = RegisterArea(body.area)
        return await gateway.modbus_diag.read(
            body.device, body.unit_id, area, body.address, body.count
        )

    @app.post("/api/modbus/write")
    async def api_modbus_write(body: ModbusWriteBody, user: str = Depends(_session)) -> dict[str, Any]:
        if not gateway.modbus_diag:
            raise HTTPException(503, "Not ready")
        area = RegisterArea(body.area)
        return await gateway.modbus_diag.write(
            body.device, body.unit_id, area, body.address, body.values
        )

    @app.post("/api/opcua/read")
    async def api_opcua_read(body: OpcUaReadBody) -> dict[str, Any]:
        client = gateway.opcua_clients[0] if gateway.opcua_clients else None
        if not client:
            raise HTTPException(503, "No OPC UA client")
        val = await client.read(body.node_id)
        return {"value": val}

    @app.post("/api/opcua/write")
    async def api_opcua_write(body: OpcUaWriteBody, user: str = Depends(_session)) -> dict[str, Any]:
        client = gateway.opcua_clients[0] if gateway.opcua_clients else None
        if not client:
            raise HTTPException(503, "No OPC UA client")
        await client.write(body.node_id, body.value)
        return {"ok": True}

    @app.get("/api/communication")
    async def api_comm(limit: int = 200) -> list[dict[str, Any]]:
        return gateway.comm_monitor.export(limit)

    @app.post("/api/communication/clear")
    async def api_comm_clear(user: str = Depends(_session)) -> dict[str, Any]:
        if gateway.authz and not gateway.authz.can_write(user):
            raise HTTPException(403, "Forbidden")
        gateway.comm_monitor.clear()
        return {"ok": True}

    @app.get("/api/trends")
    async def api_trends() -> dict[str, Any]:
        return gateway.trends.snapshot()

    @app.get("/api/trends/{tag_name}")
    async def api_trend_tag(tag_name: str, limit: int = 120) -> list[dict[str, Any]]:
        return gateway.trends.series(tag_name, limit)

    @app.get("/api/history")
    async def api_history(
        device: str | None = None,
        tag: str | None = None,
        limit: int = 500,
    ) -> list[dict[str, Any]]:
        return gateway.history.query(device=device, tag=tag, limit=limit)

    @app.get("/api/audit")
    async def api_audit() -> list[dict[str, Any]]:
        return gateway.audit.list_records()

    @app.get("/api/certificates")
    async def api_certs() -> dict[str, Any]:
        return gateway.certs.list_all()

    @app.post("/api/auth/login")
    async def api_login(body: LoginBody) -> dict[str, Any]:
        sess = gateway.auth.login(body.username, body.password) if gateway.auth else None
        if not sess:
            raise HTTPException(401, "Invalid credentials")
        return {"token": sess.token, "username": sess.username}

    config_router = APIRouter(prefix="/api/config")
    register_config_routes(config_router, gateway, _session)
    app.include_router(config_router)

    app.include_router(ws_router)
    from app.api import websocket as ws_mod

    ws_mod.attach_websocket(ws_router, gateway)
    return app
