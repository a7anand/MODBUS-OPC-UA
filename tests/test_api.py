# Copyright (c) 2026 Aman Anand, M (T&I), Barauni

from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient

from app.api.app import create_app
from app.core.gateway import Gateway

from tests.test_paths import TEST_GATEWAY_YAML


@pytest.mark.asyncio
async def test_api_status():
    gw = Gateway(TEST_GATEWAY_YAML)
    await gw.load()
    app = create_app(gw)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/status")
        assert resp.status_code == 200
        assert "gateway" in resp.json()
        home = await client.get("/")
        assert home.status_code == 200
        assert "BKPL-GATEWAY" in home.text or "Dashboard" in home.text
