# Copyright (c) 2026 Aman Anand, M (T&I), Barauni
import pytest
from httpx import ASGITransport, AsyncClient

from app.api.app import create_app
from app.core.gateway import Gateway

from tests.test_paths import TEST_GATEWAY_YAML


@pytest.mark.asyncio
async def test_login_when_auth_disabled():
    gw = Gateway(TEST_GATEWAY_YAML)
    await gw.load()
    app = create_app(gw)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/api/auth/login", json={"username": "x", "password": "y"})
        # With require_auth false, login may still fail without users — endpoint exists
        assert resp.status_code in (200, 401)
    await gw.stop()
