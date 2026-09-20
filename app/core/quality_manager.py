# Copyright (c) 2026 Aman Anand, M (T&I), Barauni
"""Tag quality transitions and events."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from app.core.enums import TagQuality


@dataclass
class QualityChange:
    tag_name: str
    old: TagQuality
    new: TagQuality
    reason: str


class QualityManager:
    def __init__(self) -> None:
        self._listeners: list[Callable[[QualityChange], None]] = []

    def subscribe(self, listener: Callable[[QualityChange], None]) -> None:
        self._listeners.append(listener)

    def transition(
        self, tag_name: str, current: TagQuality, new: TagQuality, reason: str
    ) -> TagQuality:
        if current == new:
            return current
        change = QualityChange(tag_name, current, new, reason)
        for listener in self._listeners:
            listener(change)
        return new

    def on_comm_failure(self, tag_name: str, current: TagQuality) -> TagQuality:
        return self.transition(
            tag_name,
            current,
            TagQuality.COMMUNICATION_FAILURE,
            "communication failure",
        )

    def on_comm_restored(self, tag_name: str, current: TagQuality) -> TagQuality:
        if current == TagQuality.COMMUNICATION_FAILURE:
            return self.transition(tag_name, current, TagQuality.GOOD, "communication restored")
        return current
