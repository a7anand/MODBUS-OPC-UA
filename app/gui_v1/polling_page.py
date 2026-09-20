# Copyright (c) 2026 Aman Anand, M (T&I), Barauni
"""Poll group intervals — /api/config/poll-groups."""

from __future__ import annotations

from PyQt5.QtWidgets import (
    QHBoxLayout,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.gui_shared.api_client import ApiError, GatewayApiClient


class PollingPage(QWidget):
    def __init__(self, api: GatewayApiClient, parent=None) -> None:
        super().__init__(parent)
        self._api = api
        layout = QVBoxLayout(self)
        self.table = QTableWidget(0, 2)
        self.table.setHorizontalHeaderLabels(["Group ID", "Interval (ms)"])
        layout.addWidget(self.table)
        save = QPushButton("Save selected row interval")
        save.clicked.connect(self._save)
        layout.addWidget(save)

    def refresh(self) -> None:
        try:
            groups = self._api.get("/api/config/poll-groups") or []
        except Exception:
            return
        self.table.setRowCount(len(groups))
        for row, g in enumerate(groups):
            self.table.setItem(row, 0, QTableWidgetItem(str(g["id"])))
            spin = QSpinBox()
            spin.setRange(50, 3600000)
            spin.setValue(int(g["interval_ms"]))
            self.table.setCellWidget(row, 1, spin)

    def _save(self) -> None:
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.information(self, "Polling", "Select a poll group row.")
            return
        gid = self.table.item(row, 0).text()
        spin = self.table.cellWidget(row, 1)
        if not isinstance(spin, QSpinBox):
            return
        try:
            self._api.put(f"/api/config/poll-groups/{gid}", {"interval_ms": spin.value()})
            QMessageBox.information(self, "Polling", "Saved — gateway reloaded polling.")
        except ApiError as exc:
            QMessageBox.warning(self, "Polling", str(exc))
