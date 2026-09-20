# Copyright (c) 2026 Aman Anand, M (T&I), Barauni
from __future__ import annotations

from PyQt5.QtWidgets import QVBoxLayout

from app.gui_v2.pages.base import PageBase
from app.gui_v2.widgets import SectionHeader
from app.gui_v1.import_page import ImportPage


class ImportExportPage(PageBase):
    screen_id = "tags_import"
    breadcrumb = "Tags / Import / Export"

    def __init__(self, api, theme, parent=None) -> None:
        super().__init__(api, theme, parent)
        layout = QVBoxLayout(self)
        layout.addWidget(SectionHeader("Tag Import / Export", theme))
        self._embed = ImportPage(api)
        layout.addWidget(self._embed)

    def refresh(self) -> None:
        if hasattr(self._embed, "refresh"):
            self._embed.refresh()
