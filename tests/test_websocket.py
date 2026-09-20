# Copyright (c) 2026 Aman Anand, M (T&I), Barauni
import pytest

from app.api.app import create_app
from app.core.gateway import Gateway

from tests.test_paths import TEST_GATEWAY_YAML


@pytest.mark.asyncio
async def test_websocket_route_registered():
    gw = Gateway(TEST_GATEWAY_YAML)
    await gw.load()
    app = create_app(gw)
    paths = {getattr(r, "path", "") for r in app.routes}
    assert "/ws" in paths or any("ws" in p for p in paths)
    await gw.stop()
