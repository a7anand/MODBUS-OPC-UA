# Copyright (c) 2026 Aman Anand, M (T&I), Barauni
from __future__ import annotations

from PyQt5.QtWidgets import QLabel

from app.gui.theme import ThemeManager

_ICONS = {"good": "●", "bad": "●", "warn": "▲", "neutral": "○", "accent": "◆"}


class StatusBadge(QLabel):
    """Icon + text + color for operational states."""

    def __init__(self, text: str, theme: ThemeManager, state: str = "neutral", parent=None) -> None:
        super().__init__(parent)
        self._theme = theme
        self._state = state
        self._caption = text
        theme.theme_changed.connect(lambda _: self._restyle())
        self._restyle()

    def set_state(self, text: str, state: str) -> None:
        self._caption = text
        self._state = state
        self._restyle()

    def _restyle(self) -> None:
        p = self._theme.palette()
        sym = _ICONS.get(self._state, "○")
        color = p["muted"]
        if self._state == "good":
            color = p["good"]
        elif self._state == "bad":
            color = p["bad"]
        elif self._state == "warn":
            color = p["warn"]
        elif self._state == "accent":
            color = p["accent"]
        self.setText(f"{sym} {self._caption}")
        self.setStyleSheet(
            f"padding: 2px 6px; border: 1px solid {p['border']}; "
            f"background: {p['panel_alt']}; color: {color}; font-weight: 600;"
        )
