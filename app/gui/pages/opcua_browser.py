# Copyright (c) 2026 Aman Anand, M (T&I), Barauni
from __future__ import annotations

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QFormLayout,
    QGroupBox,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
)

from app.gui.pages.base import PageBase
from app.gui.widgets import SectionHeader, StatusBadge


class OpcUaBrowserPage(PageBase):
    screen_id = "diag_opcua"
    breadcrumb = "Diagnostics / OPC UA Browser"

    def __init__(self, api, theme, parent=None) -> None:
        super().__init__(api, theme, parent)
        layout = QVBoxLayout(self)
        layout.addWidget(SectionHeader("OPC UA Address Space", theme))
        self.status = StatusBadge("Server", theme, "neutral")
        layout.addWidget(self.status)

        split = QSplitter()
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Browse Name"])
        self.tree.currentItemChanged.connect(self._on_node)
        split.addWidget(self.tree)

        info_box = QGroupBox("Node Information")
        form = QFormLayout(info_box)
        self.fields = {k: QTableWidgetItem("") for k in ("node_id", "browse", "display", "datatype")}
        # use labels instead
        from PyQt5.QtWidgets import QLabel

        self.lbl = {k: QLabel("—") for k in ("NodeId", "Browse Name", "Display Name", "Data Type", "Access", "Value")}
        for k, w in self.lbl.items():
            form.addRow(k, w)
        split.addWidget(info_box)
        split.setSizes([360, 640])
        layout.addWidget(split)

        layout.addWidget(SectionHeader("Subscription Monitor", theme))
        self.subs = QTableWidget(0, 4)
        self.subs.setHorizontalHeaderLabels(["NodeId", "Value", "Status", "Timestamp"])
        layout.addWidget(self.subs)

    def refresh(self) -> None:
        try:
            st = self.api.get("/api/opcua/status") or {}
            running = bool(st.get("server_running"))
            ep = st.get("server_endpoint") or "—"
            self.status.set_state(
                f"{'RUNNING' if running else 'STOPPED'} — {ep}",
                "good" if running else "bad",
            )
            nodes = self.api.get("/api/opcua/browse") or []
        except Exception as exc:
            self.status.set_state(str(exc), "bad")
            return
        self.tree.clear()
        for n in nodes:
            item = QTreeWidgetItem([str(n.get("browse_name", ""))])
            item.setData(0, Qt.UserRole, n)
            self.tree.addTopLevelItem(item)

    def _on_node(self, current: QTreeWidgetItem | None, _prev: QTreeWidgetItem | None) -> None:
        if not current:
            return
        n = current.data(0, Qt.UserRole) or {}
        self.lbl["NodeId"].setText(str(n.get("node_id", "")))
        self.lbl["Browse Name"].setText(str(n.get("browse_name", "")))
        self.lbl["Display Name"].setText(str(n.get("display_name", n.get("browse_name", ""))))
        self.lbl["Data Type"].setText(str(n.get("datatype", "")))
        self.lbl["Access"].setText(str(n.get("access", "")))
        self.lbl["Value"].setText(str(n.get("value", "")))
