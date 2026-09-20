# Copyright (c) 2026 Aman Anand, M (T&I), Barauni
"""OPC UA client → tag DB / Modbus (PDF TEST 2 path)."""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING, Any

from app.core.enums import TagQuality
from app.opcua.subscriptions import OpcUaSubscriptionManager

if TYPE_CHECKING:
    from app.core.gateway import Gateway

logger = logging.getLogger(__name__)


class OpcUaClientSyncService:
    def __init__(self, gateway: Gateway) -> None:
        self._gw = gateway
        self._subs = OpcUaSubscriptionManager()
        self._poll_task: asyncio.Task | None = None

    async def start(self) -> None:
        await self._subs.stop_all()
        for client in self._gw.opcua_clients:
            entries = [
                (s.node_id, s.tag_name)
                for s in client.config.subscriptions
                if s.node_id and s.tag_name
            ]
            if entries:

                def _on(tag_name: str, value: Any) -> None:
                    asyncio.create_task(self._handle_value(tag_name, value))

                await self._subs.start_for_client(client, entries, _on)
        if not self._poll_task or self._poll_task.done():
            self._poll_task = asyncio.create_task(self._poll_loop())

    async def stop(self) -> None:
        if self._poll_task:
            self._poll_task.cancel()
            try:
                await self._poll_task
            except asyncio.CancelledError:
                pass
        await self._subs.stop_all()

    async def _poll_loop(self) -> None:
        while True:
            await asyncio.sleep(1.0)
            for client in self._gw.opcua_clients:
                if not client._client:
                    continue
                for sub in client.config.subscriptions:
                    try:
                        val = await client.read(sub.node_id)
                        await self._handle_value(sub.tag_name, val)
                    except Exception as exc:  # noqa: BLE001
                        logger.debug("UA poll %s: %s", sub.tag_name, exc)

    async def _handle_value(self, tag_name: str, value: Any) -> None:
        rec = self._gw.tags.get(tag_name)
        if rec is None:
            return
        self._gw.tags.update_value(tag_name, value, TagQuality.GOOD, origin="opcua_client")
        if self._gw.opcua_server:
            await self._gw.opcua_server.update_from_tag(tag_name)
        from app.core.enums import MappingDirection

        mapping = None
        if self._gw.doc:
            for m in self._gw.doc.mappings:
                if m.tag_name == tag_name and m.enabled:
                    mapping = m
                    break
        if mapping and mapping.direction in (
            MappingDirection.UA_TO_MB,
            MappingDirection.BIDIRECTIONAL,
        ):
            await self._gw.write_tag(tag_name, value, username="opcua_client")
