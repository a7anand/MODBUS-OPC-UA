# Copyright (c) 2026 Aman Anand, M (T&I), Barauni
"""V3 admin APIs: users, certificates, simulator, exports."""

from __future__ import annotations

import csv
import io
import json
import shutil
from pathlib import Path
from typing import Any, Callable

import yaml
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pydantic import BaseModel

from app.core.config_schema import SecurityUser
from app.core.enums import UserRole
from app.core.mapping_feedback import validate_mappings
from app.security.password_manager import hash_password
from app.simulator.signals import SignalEngine, SignalMode


class UserBody(BaseModel):
    username: str
    password: str = ""
    role: UserRole = UserRole.VIEWER
    enabled: bool = True


class SignalModeBody(BaseModel):
    name: str
    mode: str
    manual_value: int = 0


class CertActionBody(BaseModel):
    file: str
    store: str = "trusted"


def register_admin_routes(
    router: APIRouter,
    gateway: Any,
    session_dep: Callable[..., str],
) -> None:
    signals = SignalEngine()

    def _admin(user: str) -> None:
        if not gateway.doc or not gateway.doc.security.require_auth:
            return
        if gateway.authz and gateway.authz.role_for(user) != UserRole.ADMINISTRATOR:
            raise HTTPException(403, "Administrator required")

    @router.get("/users")
    async def list_users(user: str = Depends(session_dep)) -> list[dict[str, Any]]:
        _admin(user)
        if not gateway.doc:
            return []
        return [
            {"username": u.username, "role": u.role.value, "enabled": u.enabled}
            for u in gateway.doc.security.users
        ]

    @router.post("/users")
    async def upsert_user(body: UserBody, user: str = Depends(session_dep)) -> dict[str, Any]:
        _admin(user)
        if not gateway.doc:
            raise HTTPException(503, "Gateway not loaded")
        doc = gateway.doc.model_copy(deep=True)
        users = [u for u in doc.security.users if u.username != body.username]
        pw_hash = hash_password(body.password) if body.password else ""
        existing = next((u for u in doc.security.users if u.username == body.username), None)
        if existing and not body.password:
            pw_hash = existing.password_hash
        users.append(
            SecurityUser(
                username=body.username,
                password_hash=pw_hash,
                role=body.role,
                enabled=body.enabled,
            )
        )
        doc.security.users = users
        await gateway.persist_document(doc, user=user, description=f"user {body.username}")
        return {"ok": True}

    @router.post("/certificates/import")
    async def import_cert(
        store: str,
        file: UploadFile = File(...),
        user: str = Depends(session_dep),
    ) -> dict[str, Any]:
        _admin(user)
        if store not in ("own", "trusted", "rejected"):
            raise HTTPException(400, "Invalid store")
        dest_dir = gateway.certs.base / store
        dest_dir.mkdir(parents=True, exist_ok=True)
        name = Path(file.filename or "cert.pem").name
        path = dest_dir / name
        path.write_bytes(await file.read())
        gateway.audit.record(user, "cert_import", name, new_value=store)
        return {"ok": True, "path": str(path)}

    @router.post("/certificates/trust")
    async def trust_cert(body: CertActionBody, user: str = Depends(session_dep)) -> dict[str, Any]:
        _admin(user)
        src = gateway.certs.base / "rejected" / body.file
        if not src.exists():
            src = gateway.certs.base / "own" / body.file
        if not src.exists():
            raise HTTPException(404, "Certificate not found")
        dst = gateway.certs.base / "trusted" / body.file
        shutil.copy2(src, dst)
        return {"ok": True, "trusted": body.file}

    @router.post("/certificates/reject")
    async def reject_cert(body: CertActionBody, user: str = Depends(session_dep)) -> dict[str, Any]:
        _admin(user)
        for folder in ("trusted", "own"):
            src = gateway.certs.base / folder / body.file
            if src.exists():
                dst = gateway.certs.base / "rejected" / body.file
                shutil.copy2(src, dst)
                return {"ok": True, "rejected": body.file}
        raise HTTPException(404, "Certificate not found")

    @router.get("/simulator/signals")
    async def simulator_status() -> dict[str, Any]:
        return {"signals": signals.status()}

    @router.post("/simulator/signals/mode")
    async def set_signal_mode(
        body: SignalModeBody, user: str = Depends(session_dep)
    ) -> dict[str, Any]:
        if gateway.authz and not gateway.authz.can_write(user):
            raise HTTPException(403, "Forbidden")
        try:
            mode = SignalMode(body.mode)
        except ValueError:
            raise HTTPException(400, "Invalid mode") from None
        signals.set_mode(body.name, mode, body.manual_value)
        if gateway.modbus:
            for dev in gateway.modbus.devices.values():
                mem = getattr(dev, "_memory", None)
                if mem is not None:
                    signals.apply_to_memory(mem)
        return {"ok": True}

    @router.get("/communication/export.csv")
    async def export_comm_csv(limit: int = 1000) -> dict[str, str]:
        rows = gateway.comm_monitor.export(limit)
        buf = io.StringIO()
        if rows:
            writer = csv.DictWriter(buf, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)
        return {"content": buf.getvalue()}

    @router.post("/certificates/generate")
    async def generate_cert(user: str = Depends(session_dep)) -> dict[str, Any]:
        _admin(user)
        try:
            from app.opcua.cert_generator import generate_self_signed

            path = generate_self_signed(gateway.certs.base / "own")
        except ImportError as exc:
            raise HTTPException(
                501, "Install cryptography package for certificate generation"
            ) from exc
        gateway.audit.record(user, "cert_generate", str(path))
        return {"ok": True, "certificate": str(path)}

    @router.post("/certificates/rotate")
    async def rotate_cert(user: str = Depends(session_dep)) -> dict[str, Any]:
        _admin(user)
        try:
            from app.opcua.cert_generator import rotate_self_signed

            result = rotate_self_signed(gateway.certs.base / "own")
        except ImportError as exc:
            raise HTTPException(
                501, "Install cryptography package for certificate rotation"
            ) from exc
        gateway.audit.record(user, "cert_rotate", result["certificate"])
        return {"ok": True, **result}

    @router.get("/mappings/validate")
    async def mappings_validate() -> dict[str, Any]:
        if not gateway.doc:
            return {"valid": True, "errors": []}
        errors = validate_mappings(gateway.doc)
        return {"valid": not errors, "errors": errors}

    @router.get("/tags/export/json")
    async def export_tags_json() -> list[dict[str, Any]]:
        if not gateway.doc:
            return []
        return [t.model_dump(mode="json") for t in gateway.doc.tags]

    @router.get("/tags/export/yaml")
    async def export_tags_yaml() -> dict[str, str]:
        if not gateway.doc:
            return {"content": "tags: []\n"}
        payload = {"tags": [t.model_dump(mode="json") for t in gateway.doc.tags]}
        return {"content": yaml.safe_dump(payload, sort_keys=False)}
