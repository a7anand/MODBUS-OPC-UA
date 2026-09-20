# Copyright (c) 2026 Aman Anand, M (T&I), Barauni
"""Communication monitor + Modbus PDU hex (same data as web Traffic/Diagnostics)."""

from __future__ import annotations

from PyQt5.QtWidgets import (
    QHBoxLayout,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.gui_shared.api_client import GatewayApiClient


class CommunicationMonitorPage(QWidget):
    def __init__(self, api: GatewayApiClient, parent=None) -> None:
        super().__init__(parent)
        self._api = api
        layout = QVBoxLayout(self)
        bar = QHBoxLayout()
        clear_btn = QPushButton("Clear buffer")
        clear_btn.clicked.connect(self._clear)
        bar.addWidget(clear_btn)
        bar.addStretch()
        layout.addLayout(bar)
        self.table = QTableWidget(0, 8)
        self.table.setHorizontalHeaderLabels(
            ["Time", "Device", "Tag", "Value", "Result", "ms", "Tx hex", "Rx hex"]
        )
        self.table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table)

    def refresh(self) -> None:
        try:
            rows = self._api.get("/api/communication?limit=100") or []
        except Exception:
            return
        self.table.setRowCount(len(rows))
        for r, c in enumerate(rows):
            self.table.setItem(r, 0, QTableWidgetItem(str(c.get("timestamp", ""))))
            self.table.setItem(r, 1, QTableWidgetItem(str(c.get("device", ""))))
            self.table.setItem(r, 2, QTableWidgetItem(str(c.get("tag_name", ""))))
            self.table.setItem(r, 3, QTableWidgetItem(str(c.get("value", ""))))
            self.table.setItem(r, 4, QTableWidgetItem(str(c.get("result", ""))))
            self.table.setItem(r, 5, QTableWidgetItem(str(c.get("response_time_ms", ""))))
            self.table.setItem(r, 6, QTableWidgetItem(str(c.get("tx_hex", ""))))
            self.table.setItem(r, 7, QTableWidgetItem(str(c.get("rx_hex", ""))))

    def _clear(self) -> None:
        try:
            self._api.post("/api/communication/clear")
            self.refresh()
        except Exception:
            pass
