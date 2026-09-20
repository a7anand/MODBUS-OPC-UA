# Copyright (c) 2026 Aman Anand, M (T&I), Barauni
from __future__ import annotations

from typing import Any

from PyQt5.QtCore import QAbstractTableModel, QModelIndex, Qt, QVariant

COMM_COLUMNS = [
    "timestamp",
    "protocol",
    "device",
    "direction",
    "operation",
    "address",
    "request",
    "response",
    "result",
    "response_time_ms",
    "error",
]


class CommTraceModel(QAbstractTableModel):
    HEADERS = [
        "Timestamp",
        "Protocol",
        "Device",
        "Dir",
        "Operation",
        "Address / Node",
        "Request",
        "Response",
        "Result",
        "ms",
        "Error",
    ]

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
        row = self._rows[index.row()]
        keys = [
            "timestamp",
            "protocol",
            "device",
            "direction",
            "operation",
            "tag_name",
            "tx_hex",
            "rx_hex",
            "result",
            "response_time_ms",
            "error",
        ]
        key = keys[index.column()]
        val = row.get(key, "")
        if index.column() == 2 and not val:
            val = row.get("device", "")
        if index.column() == 3 and not val:
            val = "TX→RX" if row.get("tx_hex") else ""
        if index.column() == 4 and not val:
            val = row.get("result", "poll")
        if index.column() == 5:
            val = row.get("tag_name") or row.get("address", "")
        if index.column() == 6:
            val = row.get("tx_hex", "")
        if index.column() == 7:
            val = row.get("rx_hex", "")
        return "" if val is None else str(val)

    def row_at(self, row: int) -> dict[str, Any]:
        return self._rows[row]

    def set_rows(self, rows: list[dict[str, Any]]) -> None:
        if len(rows) == len(self._rows) and rows == self._rows:
            return
        self.beginResetModel()
        self._rows = rows
        self.endResetModel()
