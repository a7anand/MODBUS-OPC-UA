# Copyright (c) 2026 Aman Anand, M (T&I), Barauni
from __future__ import annotations

from typing import Any

from PyQt5.QtCore import QAbstractTableModel, QModelIndex, Qt, QVariant


class EventTableModel(QAbstractTableModel):
    HEADERS = ["Timestamp", "Severity", "Source", "Device", "Event", "Description", "Ack"]

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._rows: list[dict[str, Any]] = []

    def rowCount(self, parent=QModelIndex()) -> int:  # noqa: N802
        return len(self._rows)

    def columnCount(self, parent=QModelIndex()) -> int:  # noqa: N802
        return len(self.HEADERS)

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.DisplayRole):  # noqa: N802
        if role != Qt.DisplayRole or orientation != Qt.Horizontal:
            return QVariant()
        return self.HEADERS[section]

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole):  # noqa: N802
        if not index.isValid() or role != Qt.DisplayRole:
            return QVariant()
        e = self._rows[index.row()]
        cols = [
            e.get("timestamp", e.get("time", "")),
            e.get("severity", ""),
            e.get("source", "gateway"),
            e.get("device", ""),
            e.get("event", e.get("type", "")),
            e.get("message", e.get("description", "")),
            e.get("acknowledged", ""),
        ]
        return str(cols[index.column()] or "")

    def set_rows(self, rows: list[dict[str, Any]]) -> None:
        self.beginResetModel()
        self._rows = rows
        self.endResetModel()
