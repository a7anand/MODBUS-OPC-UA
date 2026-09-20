# Copyright (c) 2026 Aman Anand, M (T&I), Barauni

import asyncio
from pathlib import Path

import pytest
from asyncua import Client

from app.core.gateway import Gateway

from tests.test_paths import TEST_GATEWAY_YAML

CONFIG = TEST_GATEWAY_YAML


@pytest.mark.asyncio
async def test_gateway_polls_simulator_tag():
    gw = Gateway(CONFIG)
    await gw.load()
    gw.doc.opcua.server.endpoint = "opc.tcp://127.0.0.1:14841"
    gw.doc.web.enabled = False
    await gw.start()
    await asyncio.sleep(1.5)
    snap = gw.tags.snapshot()
    assert snap
    assert any(t["quality"] == "GOOD" for t in snap)
    await gw.stop()


@pytest.mark.asyncio
async def test_opcua_server_exposes_tag():
    gw = Gateway(CONFIG)
    await gw.load()
    gw.doc.opcua.server.endpoint = "opc.tcp://127.0.0.1:14842"
    gw.doc.web.enabled = False
    await gw.start()
    await asyncio.sleep(2)
    try:
        async with Client(url="opc.tcp://127.0.0.1:14842/") as client:
            ns = await client.get_namespace_index("urn:modbus-opcua-gateway:tags")
            node = client.get_node(f"ns={ns};s=SIM_PLC/boiler_temp")
            val = await node.read_value()
            assert val is not None
    finally:
        await gw.stop()
