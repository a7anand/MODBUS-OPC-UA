# Copyright (c) 2026 Aman Anand, M (T&I), Barauni
"""OPC UA client for outbound connections."""

from __future__ import annotations

import logging
from typing import Any

from asyncua import Client

from app.core.config_schema import OpcUaClientConfig

logger = logging.getLogger(__name__)


class OpcUaClientEngine:
    def __init__(self, config: OpcUaClientConfig) -> None:
        self.config = config
        self._client: Client | None = None

    async def connect(self) -> None:
        if not self.config.enabled:
            return
        self._client = Client(url=self.config.endpoint)
        if self.config.username:
            self._client.set_user(self.config.username)
            self._client.set_password(self.config.password or "")
        await self._client.connect()
        logger.info("OPC UA client %s connected", self.config.name)

    async def disconnect(self) -> None:
        if self._client:
            await self._client.disconnect()
        self._client = None

    async def read(self, node_id: str) -> Any:
        if not self._client:
            raise RuntimeError("client not connected")
        node = self._client.get_node(node_id)
        return await node.read_value()

    async def write(self, node_id: str, value: Any) -> None:
        if not self._client:
            raise RuntimeError("client not connected")
        node = self._client.get_node(node_id)
        await node.write_value(value)

    async def browse(self, node_id: str = "i=85") -> list[dict[str, Any]]:
        if not self._client:
            return []
        node = self._client.get_node(node_id)
        children = await node.get_children()
        out = []
        for child in children:
            bn = await child.read_browse_name()
            out.append({"node_id": str(child.nodeid), "browse_name": str(bn.Name)})
        return out
