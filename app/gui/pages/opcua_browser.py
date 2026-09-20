# Copyright (c) 2026 Aman Anand, M (T&I), Barauni
from __future__ import annotations

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSplitter,
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

        bar = QHBoxLayout()
        bar.addWidget(QLabel("Source:"))
        self.source = QLabel("server")
        bar.addWidget(self.source)
        self.btn_sub = QPushButton("Subscribe node")
        self.btn_sub.clicked.connect(self._subscribe)
        bar.addWidget(self.btn_sub)
        bar.addStretch()
        layout.addLayout(bar)

        split = QSplitter()
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Browse Name", "Node class"])
        self.tree.itemExpanded.connect(self._on_expand)
        self.tree.currentItemChanged.connect(self._on_node)
        split.addWidget(self.tree)

        self.detail = QLabel("Select a node")
        self.detail.setWordWrap(True)
        split.addWidget(self.detail)
        split.setSizes([420, 580])
        layout.addWidget(split)

        layout.addWidget(SectionHeader("Subscription Monitor", theme))
        self.subs = QTreeWidget()
        self.subs.setHeaderLabels(["NodeId", "Value", "Status", "Timestamp"])
        layout.addWidget(self.subs)

        self._selected_node: str | None = None
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._refresh_subs)
        self._timer.start(2000)

    def refresh(self) -> None:
        try:
            st = self.api.get("/api/opcua/status") or {}
            running = bool(st.get("server_running"))
            ep = st.get("server_endpoint") or "—"
            sec = st.get("security") or {}
            self.status.set_state(
                f"{'RUNNING' if running else 'STOPPED'} — {ep} — {sec.get('security_mode', '')}",
                "good" if running else "bad",
            )
        except Exception as exc:
            self.status.set_state(str(exc), "bad")
        self.tree.clear()
        self._load_children(None, "i=85")

    def _load_children(self, parent: QTreeWidgetItem | None, node_id: str) -> None:
        try:
            nodes = self.api.get(
                f"/api/opcua/browse?node_id={node_id}&source=server"
            ) or []
        except Exception:
            return
        for n in nodes:
            item = QTreeWidgetItem(
                [str(n.get("browse_name", "")), str(n.get("node_class", ""))]
            )
            item.setData(0, Qt.UserRole, n)
            if n.get("node_class") not in ("Variable", ""):
                item.addChild(QTreeWidgetItem(["…", ""]))
            if parent is None:
                self.tree.addTopLevelItem(item)
            else:
                parent.addChild(item)

    def _on_expand(self, item: QTreeWidgetItem) -> None:
        if item.childCount() == 1 and item.child(0).text(0) == "…":
            item.removeChild(item.child(0))
            n = item.data(0, Qt.UserRole) or {}
            nid = n.get("node_id")
            if nid:
                self._load_children(item, str(nid))

    def _on_node(self, current: QTreeWidgetItem | None, _prev: QTreeWidgetItem | None) -> None:
        if not current:
            return
        n = current.data(0, Qt.UserRole) or {}
        self._selected_node = str(n.get("node_id", ""))
        self.detail.setText(
            f"NodeId: {n.get('node_id')}\nBrowse: {n.get('browse_name')}\n"
            f"Class: {n.get('node_class')}\nValue: {n.get('value', '')}"
        )

    def _subscribe(self) -> None:
        if not self._selected_node:
            return
        self.api.post(
            "/api/opcua/subscriptions",
            {"node_id": self._selected_node, "source": "server"},
        )

    def _refresh_subs(self) -> None:
        try:
            rows = self.api.get("/api/opcua/subscriptions?source=server") or []
        except Exception:
            return
        self.subs.clear()
        for r in rows:
            self.subs.addTopLevelItem(
                QTreeWidgetItem(
                    [
                        str(r.get("node_id", "")),
                        str(r.get("value", "")),
                        str(r.get("status", "")),
                        str(r.get("timestamp", "")),
                    ]
                )
            )
