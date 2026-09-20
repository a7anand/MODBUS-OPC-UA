# Copyright (c) 2026 Aman Anand, M (T&I), Barauni
"""PDF §46 TEST 2 — OPC UA source → gateway client → tag/Modbus path."""

from __future__ import annotations

import asyncio
from pathlib import Path

import pytest
from asyncua import Server

from app.core.config_schema import OpcUaClientSubscription
from app.core.gateway import Gateway
from app.opcua.client import OpcUaClientEngine

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "gateway_test2_ua_to_modbus.yaml"


@pytest.mark.asyncio
async def test_2_opcua_client_updates_tag_and_modbus_mapping():
    """UA variable change is read by gateway client and applied to mapped tag (ua_to_mb)."""
    server = Server()
    await server.init()
    server.set_endpoint("opc.tcp://127.0.0.1:14870/")
    idx = await server.register_namespace("http://test.local")
    var = await server.nodes.objects.add_variable(idx, "SourceVar", 100)
    await var.set_writable()
    await server.start()
    gw = Gateway(FIXTURE)
    await gw.load()
    node_id = f"ns={var.nodeid.NamespaceIndex};i={var.nodeid.Identifier}"
    gw.doc.opcua.clients[0].subscriptions = [
        OpcUaClientSubscription(node_id=node_id, tag_name="ua_bridge")
    ]
    gw.opcua_clients = [OpcUaClientEngine(gw.doc.opcua.clients[0])]
    await gw.modbus.connect_all()
    await gw.opcua_clients[0].connect()
    if gw.ua_sync:
        await gw.ua_sync.start()
    if gw.scheduler:
        gw.scheduler.start()
    try:
        await var.write_value(4242)
        await asyncio.sleep(3.0)
        rec = gw.tags.get("ua_bridge")
        assert rec is not None
        assert int(rec.value) == 4242
    finally:
        if gw.scheduler:
            await gw.scheduler.stop()
        if gw.ua_sync:
            await gw.ua_sync.stop()
        await gw.opcua_clients[0].disconnect()
        await gw.modbus.disconnect_all()
        await server.stop()
