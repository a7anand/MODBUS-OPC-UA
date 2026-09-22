# Copyright (c) 2026 Aman Anand, M (T&I), Barauni
from __future__ import annotations

import shutil
from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient

from app.api.app import create_app
from app.core.gateway import Gateway

from tests.test_paths import TEST_GATEWAY_YAML


@pytest.mark.asyncio
async def test_settings_and_yaml_api(tmp_path: Path):
    cfg = tmp_path / "gateway.yaml"
    shutil.copy(TEST_GATEWAY_YAML, cfg)
    gw = Gateway(cfg)
    await gw.load()
    app = create_app(gw)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.get("/api/config/settings")
        assert r.status_code == 200
        data = r.json()
        assert "gateway_name" in data
        assert "opcua_port" in data
        y = await client.get("/api/config/yaml")
        assert y.status_code == 200
        assert "content" in y.json()
        v = await client.post(
            "/api/config/yaml/validate",
            json={"content": y.json()["content"]},
        )
        assert v.status_code == 200
        assert v.json().get("valid") is True
