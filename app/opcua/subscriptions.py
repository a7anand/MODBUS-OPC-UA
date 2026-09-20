# Copyright (c) 2026 Aman Anand, M (T&I), Barauni
"""OPC UA client subscriptions (PDF §8)."""

from __future__ import annotations

import logging
from typing import Any, Callable

from app.opcua.client import OpcUaClientEngine

logger = logging.getLogger(__name__)


class _GatewaySubHandler:
    """asyncua SubscriptionHandler (datachange_notification protocol)."""

    def __init__(self, tag_name: str, callback: Callable[[str, Any], None]) -> None:
        self._tag_name = tag_name
        self._callback = callback

    def datachange_notification(self, node, val, data) -> None:  # noqa: N802, ANN001
        self._callback(self._tag_name, val)


class OpcUaSubscriptionManager:
    def __init__(self) -> None:
        self._subscriptions: list[Any] = []

    async def start_for_client(
        self,
        client: OpcUaClientEngine,
        entries: list[tuple[str, str]],
        on_value: Callable[[str, Any], None],
    ) -> None:
        """Subscribe (node_id, tag_name) pairs on a connected client."""
        if not client._client:
            return
        for node_id, tag_name in entries:
            node = client._client.get_node(node_id)
            handler = _GatewaySubHandler(tag_name, on_value)
            sub = await client._client.create_subscription(500, handler)
            await sub.subscribe_data_change(node)
            self._subscriptions.append(sub)
            logger.info("OPC UA subscribe %s ← %s", tag_name, node_id)

    async def stop_all(self) -> None:
        for sub in self._subscriptions:
            try:
                await sub.delete()
            except Exception as exc:  # noqa: BLE001
                logger.debug("subscription delete: %s", exc)
        self._subscriptions.clear()
