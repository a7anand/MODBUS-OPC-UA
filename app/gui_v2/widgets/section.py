# Copyright (c) 2026 Aman Anand, M (T&I), Barauni
from __future__ import annotations

from PyQt5.QtWidgets import QLabel, QVBoxLayout, QWidget

from app.gui_v2.theme import ThemeManager


class SectionHeader(QWidget):
    def __init__(self, title: str, theme: ThemeManager, parent=None) -> None:
        super().__init__(parent)
        self._theme = theme
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 8, 0, 4)
        layout.setSpacing(4)
        self._label = QLabel(title.upper())
        self._label.setStyleSheet("font-weight: 700; font-size: 9pt;")
        self._line = QLabel()
        self._line.setFixedHeight(1)
        layout.addWidget(self._label)
        layout.addWidget(self._line)
        theme.theme_changed.connect(lambda _: self._restyle())
        self._restyle()

    def _restyle(self) -> None:
        p = self._theme.palette()
        self._label.setStyleSheet(f"font-weight: 700; color: {p['text']};")
        self._line.setStyleSheet(f"background: {p['border']};")
