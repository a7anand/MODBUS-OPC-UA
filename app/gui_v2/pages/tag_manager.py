# Copyright (c) 2026 Aman Anand, M (T&I), Barauni
from __future__ import annotations

from PyQt5.QtCore import QSortFilterProxyModel, Qt
from PyQt5.QtWidgets import (
    QAbstractItemView,
    QHBoxLayout,
    QHeaderView,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableView,
    QVBoxLayout,
)

from app.gui_v2.models.tag_table_model import TagTableModel
from app.gui_v2.pages.base import PageBase
from app.gui_v2.widgets import SectionHeader
from app.gui_shared.api_client import ApiError
from app.gui_v1.tag_manager import TagDialog


class TagManagerPage(PageBase):
    screen_id = "tags_manager"
    breadcrumb = "Tags / Tag Manager"

    def __init__(self, api, theme, parent=None) -> None:
        super().__init__(api, theme, parent)
        layout = QVBoxLayout(self)
        layout.addWidget(SectionHeader("Industrial Tag Database", theme))
        bar = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText("Search tags (name, device, address)…")
        self.search.textChanged.connect(self._filter)
        bar.addWidget(self.search, stretch=2)
        for label, slot in (
            ("Add", self._add),
            ("Edit", self._edit),
            ("Delete", self._delete),
            ("Export CSV", self._export),
        ):
            btn = QPushButton(label)
            btn.clicked.connect(slot)
            bar.addWidget(btn)
        layout.addLayout(bar)

        self._model = TagTableModel(self)
        self._proxy = QSortFilterProxyModel(self)
        self._proxy.setSourceModel(self._model)
        self._proxy.setFilterCaseSensitivity(Qt.CaseInsensitive)
        self._proxy.setFilterKeyColumn(-1)

        self.table = QTableView()
        self.table.setModel(self._proxy)
        self.table.setSortingEnabled(True)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        layout.addWidget(self.table)

    def _filter(self, text: str) -> None:
        self._proxy.setFilterFixedString(text)

    def refresh(self) -> None:
        try:
            live = self.api.get("/api/tags") or []
            defs = self.api.get("/api/config/tags/definitions") or []
            self._model.merge_live(live, defs)
        except Exception:
            pass

    def _selected_definitions(self) -> list[dict]:
        rows = sorted({i.row() for i in self.table.selectedIndexes()})
        out = []
        for r in rows:
            src = self._proxy.mapToSource(self._proxy.index(r, 0)).row()
            row = self._model.tag_at(src)
            d = row.get("_definition") or {"name": row.get("name")}
            out.append(d)
        return out

    def _add(self) -> None:
        dlg = TagDialog(self.api, parent=self)
        if dlg.exec_() != dlg.Accepted:
            return
        try:
            self.api.post("/api/config/tags/definitions", dlg.body())
            self.refresh()
        except ApiError as exc:
            QMessageBox.warning(self, "Add tag", str(exc))

    def _edit(self) -> None:
        sel = self._selected_definitions()
        if not sel:
            return
        dlg = TagDialog(self.api, existing=sel[0], parent=self)
        if dlg.exec_() != dlg.Accepted:
            return
        name = sel[0].get("name")
        try:
            self.api.put(f"/api/config/tags/definitions/{name}", dlg.body())
            self.refresh()
        except ApiError as exc:
            QMessageBox.warning(self, "Edit tag", str(exc))

    def _delete(self) -> None:
        sel = self._selected_definitions()
        if not sel:
            return
        if QMessageBox.question(self, "Delete tags", f"Delete {len(sel)} tag(s)?") != QMessageBox.Yes:
            return
        for d in sel:
            try:
                self.api.delete(f"/api/config/tags/definitions/{d.get('name')}")
            except ApiError:
                pass
        self.refresh()

    def _export(self) -> None:
        try:
            import urllib.request

            url = self.api.base + "/api/config/tags/export/csv"
            with urllib.request.urlopen(url, timeout=10) as resp:
                data = resp.read().decode("utf-8")
            from PyQt5.QtWidgets import QFileDialog

            path, _ = QFileDialog.getSaveFileName(self, "Export tags", "tags_export.csv", "CSV (*.csv)")
            if path:
                open(path, "w", encoding="utf-8").write(data)
        except Exception as exc:
            QMessageBox.warning(self, "Export", str(exc))
