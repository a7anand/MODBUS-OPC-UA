# Copyright (c) 2026 Aman Anand, M (T&I), Barauni

import pytest
from httpx import ASGITransport, AsyncClient

from app.api.app import create_app
from app.core.gateway import Gateway

from tests.test_paths import TEST_GATEWAY_YAML

CONFIG = TEST_GATEWAY_YAML


def _test_config(tmp_path, opcua_port: int) -> __import__("pathlib").Path:
    """Copy project YAML but disable OPC UA (faster, avoids port leaks between tests)."""
    import shutil

    import yaml

    cfg = tmp_path / "gateway.yaml"
    shutil.copy(CONFIG, cfg)
    doc = yaml.safe_load(cfg.read_text(encoding="utf-8"))
    doc["opcua"]["server"]["enabled"] = False
    doc["opcua"]["server"]["endpoint"] = f"opc.tcp://127.0.0.1:{opcua_port}"
    cfg.write_text(yaml.safe_dump(doc), encoding="utf-8")
    return cfg


@pytest.mark.asyncio
async def test_add_device_via_api(tmp_path):
    cfg = _test_config(tmp_path, 14841)
    gw = Gateway(cfg)
    await gw.load()
    app = create_app(gw)
    transport = ASGITransport(app=app)
    try:
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            r = await client.post(
                "/api/config/modbus/devices",
                json={
                    "name": "TEST_PLC",
                    "mode": "tcp_client",
                    "host": "10.0.0.5",
                    "port": 502,
                },
            )
            assert r.status_code == 200
            listed = await client.get("/api/config/modbus/devices")
            names = [d["name"] for d in listed.json()]
            assert "TEST_PLC" in names
    finally:
        await gw.stop()


@pytest.mark.asyncio
async def test_update_tag_via_api(tmp_path):
    cfg = _test_config(tmp_path, 14842)
    gw = Gateway(cfg)
    await gw.load()
    app = create_app(gw)
    transport = ASGITransport(app=app)
    try:
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            tag_name = gw.doc.tags[0].name
            r = await client.put(
                f"/api/config/tags/definitions/{tag_name}",
                json={
                    "name": tag_name,
                    "device": gw.doc.tags[0].device,
                    "function": 3,
                    "address": 40002,
                    "register_count": 1,
                    "datatype": "uint16",
                    "poll_group": "default",
                    "enabled": True,
                },
            )
            assert r.status_code == 200
    finally:
        await gw.stop()
