# Copyright (c) 2026 Aman Anand, M (T&I), Barauni
import asyncio
from pathlib import Path

import pytest
import yaml
from asyncua import Client

from gateway.main import run_gateway


@pytest.mark.asyncio
async def test_opcua_reads_simulated_tag(tmp_path: Path):
    base = yaml.safe_load(Path("config/gateway.yaml").read_text(encoding="utf-8"))
    base["opcua"]["endpoint_port"] = 14840
    base["health"]["port"] = 18091
    config = tmp_path / "gateway.yaml"
    config.write_text(yaml.dump(base), encoding="utf-8")

    async def run_server():
        try:
            await asyncio.wait_for(run_gateway(config), timeout=6)
        except asyncio.TimeoutError:
            pass

    task = asyncio.create_task(run_server())
    await asyncio.sleep(2)
    try:
        async with Client(url="opc.tcp://127.0.0.1:14840/") as client:
            ns = await client.get_namespace_index("urn:aa-modbus-ua:tags")
            objects = client.nodes.objects
            node = client.get_node(f"ns={ns};s=BoilerHouse/boiler_temp")
            value = await node.read_value()
            assert isinstance(value, (int, float))
    finally:
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
