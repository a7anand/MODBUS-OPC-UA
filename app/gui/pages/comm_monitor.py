# Copyright (c) 2026 Aman Anand, M (T&I), Barauni
from __future__ import annotations

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QHBoxLayout,
    QHeaderView,
    QLineEdit,
    QPushButton,
    QTableView,
    QTextEdit,
    QVBoxLayout,
)

from app.gui.models.comm_trace_model import CommTraceModel
from app.gui.pages.base import PageBase
from app.gui.widgets import SectionHeader


class CommunicationMonitorPage(PageBase):
    screen_id = "diag_comm"
    breadcrumb = "Diagnostics / Communication Monitor"

    def __init__(self, api, theme, parent=None) -> None:
        super().__init__(api, theme, parent)
        layout = QVBoxLayout(self)
        layout.addWidget(SectionHeader("Protocol Trace Console", theme))
        bar = QHBoxLayout()
        self.filter = QLineEdit()
        self.filter.setPlaceholderText("Filter device / tag / result…")
        self.pause_btn = QPushButton("Pause")
        self.pause_btn.setCheckable(True)
        clear_btn = QPushButton("Clear")
        clear_btn.clicked.connect(self._clear)
        bar.addWidget(self.filter, stretch=2)
        bar.addWidget(self.pause_btn)
        bar.addWidget(clear_btn)
        layout.addLayout(bar)

        self._model = CommTraceModel(self)
        self.table = QTableView()
        self.table.setModel(self._model)
        self.table.setAlternatingRowColors(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.table.doubleClicked.connect(self._show_detail)
        layout.addWidget(self.table, stretch=3)

        layout.addWidget(SectionHeader("Transaction Detail", theme))
        self.detail = QTextEdit()
        self.detail.setReadOnly(True)
        layout.addWidget(self.detail, stretch=1)
        self._paused = False
        self._auto_scroll = True

    def refresh(self) -> None:
        if self._paused or self.pause_btn.isChecked():
            return
        try:
            rows = self.api.get("/api/communication?limit=200") or []
        except Exception:
            return
        filt = self.filter.text().strip().lower()
        if filt:
            rows = [
                r
                for r in rows
                if filt in str(r).lower()
            ]
        self._model.set_rows(rows)
        if self._auto_scroll and self.table.model().rowCount():
            self.table.scrollToBottom()

    def _clear(self) -> None:
        try:
            self.api.post("/api/communication/clear")
            self._model.set_rows([])
        except Exception:
            pass

    def _show_detail(self, index) -> None:
        row = self._model.row_at(index.row())
        self.detail.setPlainText(
            f"TX: {row.get('tx_hex', '')}\n\nRX: {row.get('rx_hex', '')}\n\n"
            f"Value: {row.get('value', '')}  Result: {row.get('result', '')}  "
            f"ms: {row.get('response_time_ms', '')}"
        )
