# Copyright (c) 2026 Aman Anand, M (T&I), Barauni
from __future__ import annotations

from PyQt5.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout

from app.gui_v2.theme import ThemeManager


class KpiTile(QFrame):
    def __init__(
        self,
        title: str,
        theme: ThemeManager,
        parent=None,
        state: str = "neutral",
    ) -> None:
        super().__init__(parent)
        self._theme = theme
        self._state = state
        self.setFrameShape(QFrame.StyledPanel)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(2)
        self._title = QLabel(title.upper())
        self._title.setStyleSheet("font-size: 8pt; font-weight: 600;")
        self._value = QLabel("—")
        self._value.setStyleSheet("font-size: 14pt; font-weight: 700;")
        self._hint = QLabel("")
        self._hint.setStyleSheet("font-size: 8pt;")
        layout.addWidget(self._title)
        layout.addWidget(self._value)
        layout.addWidget(self._hint)
        theme.theme_changed.connect(lambda _: self._restyle())
        self._restyle()

    def set_value(self, text: str, hint: str = "", state: str | None = None) -> None:
        self._value.setText(text)
        self._hint.setText(hint)
        if state is not None:
            self._state = state
            self._restyle()

    def _restyle(self) -> None:
        p = self._theme.palette()
        color = p["text"]
        if self._state == "good":
            color = p["good"]
        elif self._state == "bad":
            color = p["bad"]
        elif self._state == "warn":
            color = p["warn"]
        elif self._state == "accent":
            color = p["accent"]
        self.setStyleSheet(
            f"KpiTile {{ background: {p['panel']}; border: 1px solid {p['border']}; }}"
        )
        self._value.setStyleSheet(f"font-size: 14pt; font-weight: 700; color: {color};")
        self._hint.setStyleSheet(f"font-size: 8pt; color: {p['muted']};")
        self._title.setStyleSheet(f"font-size: 8pt; font-weight: 600; color: {p['muted']};")
