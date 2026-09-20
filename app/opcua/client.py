# Copyright (c) 2026 Aman Anand, M (T&I), Barauni
"""OPC UA client for outbound connections."""

from __future__ import annotations

import logging
from typing import Any

from pathlib import Path

from asyncua import Client

from app.core.config_schema import OpcUaClientConfig
from app.core.enums import OpcUaSecurityMode
from app.opcua.security_setup import apply_client_security

logger = logging.getLogger(__name__)


class OpcUaClientEngine:
    def __init__(
        self,
        config: OpcUaClientConfig,
        cert_base: Path | None = None,
    ) -> None:
        self.config = config
        self._cert_base = cert_base or Path("certificates")
        self._client: Client | None = None

    async def connect(self) -> None:
        if not self.config.enabled:
            return
        self._client = Client(url=self.config.endpoint)
        if self.config.username:
            self._client.set_user(self.config.username)
            self._client.set_password(self.config.password or "")
        if self.config.security_mode != OpcUaSecurityMode.NONE:
            await apply_client_security(
                self._client, self.config.security_mode, self._cert_base
            )
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
        return await self.browse_children(node_id)

    async def browse_children(self, node_id: str = "i=85") -> list[dict[str, Any]]:
        if not self._client:
            return []
        node = self._client.get_node(node_id)
        children = await node.get_children()
        out: list[dict[str, Any]] = []
        for child in children:
            bn = await child.read_browse_name()
            try:
                dn = await child.read_display_name()
                display = str(dn.Text)
            except Exception:  # noqa: BLE001
                display = str(bn.Name)
            try:
                nclass = await child.read_node_class()
                nc = nclass.name
            except Exception:  # noqa: BLE001
                nc = ""
            entry: dict[str, Any] = {
                "node_id": str(child.nodeid),
                "browse_name": str(bn.Name),
                "display_name": display,
                "node_class": nc,
            }
            if nc == "Variable":
                try:
                    entry["value"] = await child.read_value()
                except Exception:  # noqa: BLE001
                    pass
            out.append(entry)
        return out
