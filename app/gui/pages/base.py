# Copyright (c) 2026 Aman Anand, M (T&I), Barauni
from __future__ import annotations

from collections.abc import Callable

from PyQt5.QtWidgets import QWidget

from app.gui.theme import ThemeManager
from app.gui_shared.api_client import GatewayApiClient


class PageBase(QWidget):
    screen_id = ""
    breadcrumb = ""

    def __init__(self, api: GatewayApiClient, theme: ThemeManager, parent=None) -> None:
        super().__init__(parent)
        self.api = api
        self.theme = theme

    def refresh(self) -> None:
        """Called on timer when page is visible."""

    def toolbar_actions(self) -> list[tuple[str, Callable[[], None]]]:
        return []
