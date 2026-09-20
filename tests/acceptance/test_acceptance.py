# Copyright (c) 2026 Aman Anand, M (T&I), Barauni
"""Acceptance tests (master prompt §46)."""

from __future__ import annotations

import asyncio
from pathlib import Path

import pytest
from asyncua import Client
from httpx import ASGITransport, AsyncClient

from app.api.app import create_app
from app.core.gateway import Gateway

from tests.test_paths import TEST_GATEWAY_YAML

CONFIG = TEST_GATEWAY_YAML


@pytest.mark.asyncio
async def test_1_modbus_sim_to_opcua_server():
    """TEST 1: Simulator → Gateway → OPC UA Server → client read."""
    gw = Gateway(CONFIG)
    await gw.load()
    gw.doc.opcua.server.endpoint = "opc.tcp://127.0.0.1:14850"
    gw.doc.web.enabled = False
    await gw.start()
    await asyncio.sleep(2)
    try:
        async with Client(url="opc.tcp://127.0.0.1:14850/") as client:
            ns = await client.get_namespace_index("urn:modbus-opcua-gateway:tags")
            node = client.get_node(f"ns={ns};s=SIM_PLC/boiler_temp")
            val = await node.read_value()
            assert val is not None
    finally:
        await gw.stop()


@pytest.mark.asyncio
async def test_4_device_failure_gateway_responsive():
    """TEST 4: Bad device does not crash gateway process."""
    gw = Gateway(CONFIG)
    await gw.load()
    gw.doc.web.enabled = False
    gw.doc.opcua.server.enabled = False
    await gw.start()
    snap = gw.tags.snapshot()
    assert snap
    await gw.stop()


@pytest.mark.asyncio
async def test_5_web_config_visible_in_api():
    """TEST 5/6: API reflects gateway state."""
    gw = Gateway(CONFIG)
    await gw.load()
    app = create_app(gw)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        st = await client.get("/api/status")
        assert st.status_code == 200
        tags = await client.get("/api/tags")
        assert tags.status_code == 200
        assert isinstance(tags.json(), list)


@pytest.mark.asyncio
async def test_7_backup_list():
    gw = Gateway(CONFIG)
    await gw.load()
    gw.config_manager.backup_active(gw.config_path, user="test")
    items = gw.backups.list_backups()
    assert items
