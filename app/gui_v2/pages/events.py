# Copyright (c) 2026 Aman Anand, M (T&I), Barauni
from __future__ import annotations

from PyQt5.QtWidgets import QHBoxLayout, QHeaderView, QLineEdit, QPushButton, QTableView, QVBoxLayout

from app.gui_v2.models.event_table_model import EventTableModel
from app.gui_v2.pages.base import PageBase
from app.gui_v2.widgets import SectionHeader


class EventsAlarmsPage(PageBase):
    screen_id = "events"
    breadcrumb = "Events & Alarms"

    def __init__(self, api, theme, parent=None) -> None:
        super().__init__(api, theme, parent)
        layout = QVBoxLayout(self)
        layout.addWidget(SectionHeader("Engineering Event Log", theme))
        bar = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText("Search events…")
        export_btn = QPushButton("Export")
        bar.addWidget(self.search, stretch=2)
        bar.addWidget(export_btn)
        layout.addLayout(bar)
        self._model = EventTableModel(self)
        self.table = QTableView()
        self.table.setModel(self._model)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.table)

    def refresh(self) -> None:
        try:
            rows = self.api.get("/api/events") or []
        except Exception:
            return
        q = self.search.text().strip().lower()
        if q:
            rows = [r for r in rows if q in str(r).lower()]
        self._model.set_rows(rows)
