# Copyright (c) 2026 Aman Anand, M (T&I), Barauni
"""Dashboard — gateway status, live tags, recent events."""

from __future__ import annotations

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.gui_shared.api_client import GatewayApiClient


class DashboardPage(QWidget):
    def __init__(self, api: GatewayApiClient, parent=None) -> None:
        super().__init__(parent)
        self._api = api
        layout = QVBoxLayout(self)
        self.status = QLabel("Connecting to gateway API…")
        layout.addWidget(self.status)
        self.tags = QTableWidget(0, 5)
        self.tags.setHorizontalHeaderLabels(
            ["Name", "Device", "Value", "Quality", "Datatype"]
        )
        self.tags.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.tags, stretch=3)
        self.events = QTableWidget(0, 2)
        self.events.setHorizontalHeaderLabels(["Severity", "Message"])
        self.events.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.events, stretch=1)

    def refresh(self) -> None:
        try:
            st = self._api.get("/api/status")
            health = (st or {}).get("health") or {}
            uptime = health.get("uptime_sec", 0)
            gw = (st or {}).get("gateway") or {}
            self.status.setText(
                f"{gw.get('name', 'Gateway')} — uptime {int(uptime)}s — "
                f"{st.get('tags_count', 0)} tags"
            )
        except Exception as exc:
            self.status.setText(str(exc))
            return
        try:
            tags = self._api.get("/api/tags") or []
            self.tags.setRowCount(len(tags))
            for row, t in enumerate(tags):
                self.tags.setItem(row, 0, QTableWidgetItem(str(t.get("name", ""))))
                self.tags.setItem(row, 1, QTableWidgetItem(str(t.get("device", ""))))
                self.tags.setItem(row, 2, QTableWidgetItem(str(t.get("value", ""))))
                self.tags.setItem(row, 3, QTableWidgetItem(str(t.get("quality", ""))))
                self.tags.setItem(row, 4, QTableWidgetItem(str(t.get("datatype", ""))))
        except Exception:
            pass
        try:
            evs = self._api.get("/api/events") or []
            show = evs[:30]
            self.events.setRowCount(len(show))
            for row, e in enumerate(show):
                self.events.setItem(row, 0, QTableWidgetItem(str(e.get("severity", ""))))
                self.events.setItem(row, 1, QTableWidgetItem(str(e.get("message", ""))))
        except Exception:
            pass
