# Copyright (c) 2026 Aman Anand, M (T&I), Barauni
"""OPC UA engine abstraction."""

from __future__ import annotations

import abc
from typing import Any


class OpcUaEndpoint(abc.ABC):
    @abc.abstractmethod
    async def start(self) -> None: ...

    @abc.abstractmethod
    async def stop(self) -> None: ...

    @abc.abstractmethod
    async def write_node(self, node_id: str, value: Any) -> None: ...

    @abc.abstractmethod
    async def browse(self, node_id: str = "i=85") -> list[dict[str, Any]]: ...
