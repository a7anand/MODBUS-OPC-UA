# Copyright (c) 2026 Aman Anand, M (T&I), Barauni
"""OPC UA server browse — GET /api/opcua/browse."""

from __future__ import annotations

from PyQt5.QtWidgets import QLabel, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget

from app.gui_shared.api_client import GatewayApiClient


class OpcUaBrowserPage(QWidget):
    def __init__(self, api: GatewayApiClient, parent=None) -> None:
        super().__init__(parent)
        self._api = api
        layout = QVBoxLayout(self)
        self.status = QLabel("")
        layout.addWidget(self.status)
        self.table = QTableWidget(0, 2)
        self.table.setHorizontalHeaderLabels(["Browse name", "NodeId"])
        layout.addWidget(self.table)

    def refresh(self) -> None:
        try:
            st = self._api.get("/api/opcua/status") or {}
            ep = st.get("server_endpoint") or "not running"
            self.status.setText(
                f"Server running: {st.get('server_running')} — {ep}"
            )
            nodes = self._api.get("/api/opcua/browse") or []
        except Exception as exc:
            self.status.setText(str(exc))
            return
        self.table.setRowCount(len(nodes))
        for row, n in enumerate(nodes):
            self.table.setItem(row, 0, QTableWidgetItem(str(n.get("browse_name", ""))))
            self.table.setItem(row, 1, QTableWidgetItem(str(n.get("node_id", ""))))
