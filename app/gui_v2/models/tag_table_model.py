# Copyright (c) 2026 Aman Anand, M (T&I), Barauni
"""High-performance tag table — QAbstractTableModel with row-level patching."""

from __future__ import annotations

from typing import Any

from PyQt5.QtCore import QAbstractTableModel, QModelIndex, Qt, QVariant

COLUMNS = [
    ("name", "Tag Name"),
    ("description", "Description"),
    ("device", "Device"),
    ("protocol", "Protocol"),
    ("address_display", "Address"),
    ("datatype", "Data Type"),
    ("raw_value", "Raw Value"),
    ("value", "Engineering Value"),
    ("engineering_unit", "Unit"),
    ("quality", "Quality"),
    ("timestamp", "Timestamp"),
    ("opcua_node", "OPC UA Node"),
    ("direction", "Direction"),
    ("poll_interval", "Poll Interval"),
    ("enabled", "Enabled"),
    ("mapping", "Mapping"),
]


class TagTableModel(QAbstractTableModel):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._rows: list[dict[str, Any]] = []
        self._index_by_name: dict[str, int] = {}

    def rowCount(self, parent=QModelIndex()) -> int:  # noqa: N802
        return len(self._rows)

    def columnCount(self, parent=QModelIndex()) -> int:  # noqa: N802
        return len(COLUMNS)

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.DisplayRole):  # noqa: N802
        if role != Qt.DisplayRole or orientation != Qt.Horizontal:
            return QVariant()
        return COLUMNS[section][1]

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole):  # noqa: N802
        if not index.isValid() or role not in (Qt.DisplayRole, Qt.ToolTipRole):
            return QVariant()
        row = self._rows[index.row()]
        key = COLUMNS[index.column()][0]
        val = row.get(key, "")
        if key == "enabled":
            return "Yes" if val else "No"
        return "" if val is None else str(val)

    def flags(self, index: QModelIndex) -> Qt.ItemFlags:  # noqa: N802
        if not index.isValid():
            return Qt.NoItemFlags
        base = Qt.ItemIsSelectable | Qt.ItemIsEnabled
        if COLUMNS[index.column()][0] in ("description", "enabled"):
            return base | Qt.ItemIsEditable
        return base

    def tag_at(self, row: int) -> dict[str, Any]:
        return self._rows[row]

    def replace_all(self, rows: list[dict[str, Any]]) -> None:
        self.beginResetModel()
        self._rows = rows
        self._index_by_name = {r["name"]: i for i, r in enumerate(rows) if r.get("name")}
        self.endResetModel()

    def merge_live(self, live: list[dict[str, Any]], definitions: list[dict[str, Any]]) -> None:
        def_map = {d.get("name"): d for d in definitions}
        merged: dict[str, dict[str, Any]] = {}
        for d in definitions:
            name = d.get("name")
            if not name:
                continue
            merged[name] = self._row_from_def(d)
        for t in live:
            name = t.get("name")
            if not name:
                continue
            base = merged.get(name) or self._row_from_def(def_map.get(name) or {"name": name})
            base.update(
                {
                    "value": t.get("value"),
                    "raw_value": t.get("value"),
                    "quality": t.get("quality"),
                    "timestamp": t.get("timestamp"),
                    "device": t.get("device", base.get("device")),
                    "protocol": t.get("protocol", base.get("protocol")),
                    "datatype": t.get("datatype", base.get("datatype")),
                    "engineering_unit": t.get("engineering_unit", base.get("engineering_unit")),
                    "opcua_node": t.get("opcua_node", base.get("opcua_node")),
                    "enabled": t.get("enabled", base.get("enabled")),
                }
            )
            merged[name] = base
        ordered = sorted(merged.values(), key=lambda r: str(r.get("name", "")).lower())
        if not self._rows:
            self.replace_all(ordered)
            return
        old_names = [r.get("name") for r in self._rows]
        new_names = [r.get("name") for r in ordered]
        if old_names != new_names:
            self.replace_all(ordered)
            return
        for i, row in enumerate(ordered):
            if self._rows[i] != row:
                self._rows[i] = row
                top_left = self.index(i, 0)
                bottom_right = self.index(i, self.columnCount() - 1)
                self.dataChanged.emit(top_left, bottom_right, [Qt.DisplayRole])

    @staticmethod
    def _row_from_def(d: dict[str, Any]) -> dict[str, Any]:
        writable = bool(d.get("writable"))
        return {
            "name": d.get("name", ""),
            "description": d.get("description", ""),
            "device": d.get("device", ""),
            "protocol": d.get("protocol", "modbus"),
            "address_display": d.get("address_display") or d.get("address", ""),
            "datatype": d.get("datatype", ""),
            "raw_value": "",
            "value": "",
            "engineering_unit": d.get("engineering_unit", ""),
            "quality": "",
            "timestamp": "",
            "opcua_node": d.get("opcua_node", ""),
            "direction": "R/W" if writable else "R",
            "poll_interval": d.get("poll_group", ""),
            "enabled": d.get("enabled", True),
            "mapping": "OK" if d.get("name") else "",
            "_definition": d,
        }
