# Copyright (c) 2026 Aman Anand, M (T&I), Barauni
"""Centralized Qt style sheets — Dark / Light / System engineering themes."""

from __future__ import annotations

from enum import Enum

from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtWidgets import QApplication


class ThemeId(str, Enum):
    DARK = "dark"
    LIGHT = "light"
    SYSTEM = "system"


_PALETTES = {
    ThemeId.DARK: {
        "bg": "#1a1d21",
        "panel": "#23272e",
        "panel_alt": "#2c313a",
        "border": "#3a3f47",
        "text": "#e8eaed",
        "muted": "#9aa0a6",
        "accent": "#4a9eff",
        "good": "#3dba6c",
        "bad": "#e55353",
        "warn": "#e6a23c",
        "uncertain": "#c9a227",
    },
    ThemeId.LIGHT: {
        "bg": "#eef0f2",
        "panel": "#ffffff",
        "panel_alt": "#f4f5f7",
        "border": "#c8ccd0",
        "text": "#1a1d21",
        "muted": "#5f6368",
        "accent": "#1565c0",
        "good": "#1e7e34",
        "bad": "#c62828",
        "warn": "#ef6c00",
        "uncertain": "#b8860b",
    },
}


def _build_qss(p: dict[str, str]) -> str:
    return f"""
QMainWindow, QDialog {{
    background-color: {p['bg']};
    color: {p['text']};
}}
QWidget {{
    font-family: "Segoe UI", "Roboto", sans-serif;
    font-size: 9pt;
    color: {p['text']};
}}
QTreeWidget, QTableView, QTableWidget, QTextEdit, QPlainTextEdit, QListWidget {{
    background-color: {p['panel']};
    alternate-background-color: {p['panel_alt']};
    border: 1px solid {p['border']};
    gridline-color: {p['border']};
    selection-background-color: {p['accent']};
    selection-color: #ffffff;
}}
QHeaderView::section {{
    background-color: {p['panel_alt']};
    color: {p['text']};
    padding: 4px 6px;
    border: none;
    border-right: 1px solid {p['border']};
    border-bottom: 1px solid {p['border']};
    font-weight: 600;
}}
QToolBar {{
    background: {p['panel']};
    border-bottom: 1px solid {p['border']};
    spacing: 6px;
    padding: 2px 4px;
}}
QStatusBar {{
    background: {p['panel']};
    border-top: 1px solid {p['border']};
}}
QPushButton {{
    background-color: {p['panel_alt']};
    border: 1px solid {p['border']};
    padding: 4px 10px;
    min-height: 22px;
}}
QPushButton:hover {{
    border-color: {p['accent']};
}}
QPushButton[class="primary"] {{
    background-color: {p['accent']};
    color: #ffffff;
    font-weight: 600;
}}
QLineEdit, QSpinBox, QComboBox {{
    background-color: {p['panel']};
    border: 1px solid {p['border']};
    padding: 3px 6px;
    min-height: 22px;
}}
QGroupBox {{
    border: 1px solid {p['border']};
    margin-top: 8px;
    padding-top: 8px;
    font-weight: 600;
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    left: 8px;
    padding: 0 4px;
}}
QDockWidget {{
    titlebar-close-icon: none;
    border: 1px solid {p['border']};
}}
QScrollBar:vertical {{
    background: {p['panel']};
    width: 10px;
}}
QScrollBar::handle:vertical {{
    background: {p['border']};
    min-height: 24px;
}}
"""


class ThemeManager(QObject):
    theme_changed = pyqtSignal(str)

    def __init__(self) -> None:
        super().__init__()
        self._theme = ThemeId.DARK

    @property
    def theme_id(self) -> ThemeId:
        return self._theme

    def palette(self) -> dict[str, str]:
        if self._theme == ThemeId.SYSTEM:
            app = QApplication.instance()
            dark = False
            if app is not None:
                dark = app.palette().window().color().lightness() < 128
            return _PALETTES[ThemeId.DARK if dark else ThemeId.LIGHT]
        return _PALETTES[self._theme]

    def apply(self, app: QApplication) -> None:
        app.setStyleSheet(_build_qss(self.palette()))
        self.theme_changed.emit(self._theme.value)

    def set_theme(self, theme: ThemeId, app: QApplication) -> None:
        self._theme = theme
        self.apply(app)

    def cycle_theme(self, app: QApplication) -> None:
        order = (ThemeId.DARK, ThemeId.LIGHT, ThemeId.SYSTEM)
        idx = (order.index(self._theme) + 1) % len(order)
        self.set_theme(order[idx], app)
