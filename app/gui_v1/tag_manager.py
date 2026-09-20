# Copyright (c) 2026 Aman Anand, M (T&I), Barauni
"""Tag definitions — add / edit / delete via /api/config/tags/definitions."""

from __future__ import annotations

from PyQt5.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.gui_shared.api_client import ApiError, GatewayApiClient


class TagDialog(QDialog):
    def __init__(self, api: GatewayApiClient, existing: dict | None = None, parent=None) -> None:
        super().__init__(parent)
        self._api = api
        self.setWindowTitle("Edit tag" if existing else "Add tag")
        form = QFormLayout(self)
        self.name = QLineEdit((existing or {}).get("name", ""))
        self.device = QLineEdit((existing or {}).get("device", ""))
        self.function = QComboBox()
        for label, val in (
            ("3 — Holding", 3),
            ("4 — Input", 4),
            ("1 — Coil", 1),
            ("2 — Discrete", 2),
        ):
            self.function.addItem(label, val)
        if existing:
            idx = self.function.findData(int(existing.get("function", 3)))
            if idx >= 0:
                self.function.setCurrentIndex(idx)
        self.address = QSpinBox()
        self.address.setRange(0, 99999)
        self.address.setValue(int((existing or {}).get("address_display") or (existing or {}).get("address") or 40001))
        self.registers = QSpinBox()
        self.registers.setRange(1, 125)
        self.registers.setValue(int((existing or {}).get("register_count", 1)))
        self.datatype = QComboBox()
        for dt in ("uint16", "int16", "float32", "bool", "uint32", "int32"):
            self.datatype.addItem(dt)
        if existing:
            self.datatype.setCurrentText(str(existing.get("datatype", "uint16")))
        self.poll_group = QComboBox()
        self._load_poll_groups()
        if existing:
            self.poll_group.setCurrentText(str(existing.get("poll_group", "default")))
        self.writable = QCheckBox("Writable from OPC UA → Modbus")
        self.writable.setChecked(bool((existing or {}).get("writable")))
        self.enabled = QCheckBox("Enabled")
        self.enabled.setChecked((existing or {}).get("enabled", True) is not False)
        form.addRow("Name", self.name)
        form.addRow("Device", self.device)
        form.addRow("Function", self.function)
        form.addRow("Address", self.address)
        form.addRow("Register count", self.registers)
        form.addRow("Datatype", self.datatype)
        form.addRow("Poll group", self.poll_group)
        form.addRow("", self.writable)
        form.addRow("", self.enabled)
        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        form.addRow(buttons)

    def _load_poll_groups(self) -> None:
        self.poll_group.clear()
        try:
            for g in self._api.get("/api/config/poll-groups") or []:
                self.poll_group.addItem(f"{g['id']} ({g['interval_ms']} ms)", g["id"])
        except Exception:
            self.poll_group.addItem("default", "default")

    def body(self) -> dict:
        return {
            "name": self.name.text().strip(),
            "device": self.device.text().strip(),
            "function": int(self.function.currentData()),
            "address": self.address.value(),
            "register_count": self.registers.value(),
            "datatype": self.datatype.currentText(),
            "gain": 1.0,
            "offset": 0.0,
            "engineering_unit": "",
            "poll_group": self.poll_group.currentData() or self.poll_group.currentText().split()[0],
            "writable": self.writable.isChecked(),
            "enabled": self.enabled.isChecked(),
        }


class TagManagerPage(QWidget):
    def __init__(self, api: GatewayApiClient, parent=None) -> None:
        super().__init__(parent)
        self._api = api
        layout = QVBoxLayout(self)
        bar = QHBoxLayout()
        for text, slot in (
            ("Add tag", self._add),
            ("Edit selected", self._edit),
            ("Delete selected", self._delete),
        ):
            b = QPushButton(text)
            b.clicked.connect(slot)
            bar.addWidget(b)
        bar.addStretch()
        layout.addLayout(bar)
        self.table = QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels(
            ["Name", "Device", "Address", "Type", "Value", "Quality", "Writable"]
        )
        layout.addWidget(self.table)

    def refresh(self) -> None:
        try:
            defs = self._api.get("/api/config/tags/definitions") or []
            live = {t["name"]: t for t in (self._api.get("/api/tags") or [])}
        except Exception:
            return
        self.table.setRowCount(len(defs))
        for row, t in enumerate(defs):
            lv = live.get(t["name"], {})
            self.table.setItem(row, 0, QTableWidgetItem(str(t.get("name", ""))))
            self.table.setItem(row, 1, QTableWidgetItem(str(t.get("device", ""))))
            self.table.setItem(
                row, 2, QTableWidgetItem(str(t.get("address_display") or t.get("address", "")))
            )
            self.table.setItem(row, 3, QTableWidgetItem(str(t.get("datatype", ""))))
            self.table.setItem(row, 4, QTableWidgetItem(str(lv.get("value", ""))))
            self.table.setItem(row, 5, QTableWidgetItem(str(lv.get("quality", ""))))
            self.table.setItem(row, 6, QTableWidgetItem(str(t.get("writable", False))))

    def _selected_name(self) -> str | None:
        row = self.table.currentRow()
        if row < 0:
            return None
        return self.table.item(row, 0).text()

    def _selected_def(self) -> dict | None:
        name = self._selected_name()
        if not name:
            return None
        for t in self._api.get("/api/config/tags/definitions") or []:
            if t.get("name") == name:
                return t
        return None

    def _add(self) -> None:
        dlg = TagDialog(self._api, None, self)
        if dlg.exec_() != QDialog.Accepted:
            return
        try:
            self._api.post("/api/config/tags/definitions", dlg.body())
            self.refresh()
        except ApiError as exc:
            QMessageBox.warning(self, "Add tag", str(exc))

    def _edit(self) -> None:
        tag = self._selected_def()
        if not tag:
            QMessageBox.information(self, "Edit", "Select a tag row first.")
            return
        dlg = TagDialog(self._api, tag, self)
        if dlg.exec_() != QDialog.Accepted:
            return
        try:
            self._api.put(f"/api/config/tags/definitions/{tag['name']}", dlg.body())
            self.refresh()
        except ApiError as exc:
            QMessageBox.warning(self, "Edit tag", str(exc))

    def _delete(self) -> None:
        name = self._selected_name()
        if not name:
            return
        if QMessageBox.question(self, "Delete", f"Delete tag {name}?") != QMessageBox.Yes:
            return
        try:
            self._api.delete(f"/api/config/tags/definitions/{name}")
            self.refresh()
        except ApiError as exc:
            QMessageBox.warning(self, "Delete", str(exc))
