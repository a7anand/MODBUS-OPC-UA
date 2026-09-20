# Copyright (c) 2026 Aman Anand, M (T&I), Barauni
"""Modbus device list — add / edit / delete via /api/config/modbus/devices."""

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


class DeviceDialog(QDialog):
    def __init__(self, api: GatewayApiClient, existing: dict | None = None, parent=None) -> None:
        super().__init__(parent)
        self._api = api
        self._original_name = (existing or {}).get("name", "")
        self.setWindowTitle("Edit device" if existing else "Add device")
        form = QFormLayout(self)
        self.name = QLineEdit((existing or {}).get("name", ""))
        self.mode = QComboBox()
        for m in ("tcp_client", "tcp_server", "rtu_client", "rtu_server", "simulator"):
            self.mode.addItem(m)
        if existing:
            self.mode.setCurrentText(str(existing.get("mode", "tcp_client")))
        self.host = QLineEdit(str((existing or {}).get("host", "127.0.0.1")))
        self.port = QSpinBox()
        self.port.setRange(1, 65535)
        self.port.setValue(int((existing or {}).get("port", 502)))
        self.unit_id = QSpinBox()
        self.unit_id.setRange(0, 247)
        self.unit_id.setValue(int((existing or {}).get("unit_id", 1)))
        self.serial = QLineEdit(str((existing or {}).get("serial_port", "COM3")))
        self.polling = QCheckBox("Enable Modbus polling (connect & scan tags)")
        self.polling.setChecked((existing or {}).get("enabled", True) is not False)
        form.addRow("Name", self.name)
        form.addRow("Mode", self.mode)
        form.addRow("Host", self.host)
        form.addRow("Port", self.port)
        form.addRow("Unit ID", self.unit_id)
        form.addRow("Serial (RTU)", self.serial)
        form.addRow("", self.polling)
        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        form.addRow(buttons)

    def body(self) -> dict:
        return {
            "name": self.name.text().strip(),
            "mode": self.mode.currentText(),
            "host": self.host.text().strip(),
            "port": self.port.value(),
            "unit_id": self.unit_id.value(),
            "serial_port": self.serial.text().strip(),
            "address_base": "one",
            "enabled": self.polling.isChecked(),
        }


class DevicesPage(QWidget):
    def __init__(self, api: GatewayApiClient, parent=None) -> None:
        super().__init__(parent)
        self._api = api
        layout = QVBoxLayout(self)
        bar = QHBoxLayout()
        add_btn = QPushButton("Add device")
        add_btn.clicked.connect(self._add)
        edit_btn = QPushButton("Edit selected")
        edit_btn.clicked.connect(self._edit)
        del_btn = QPushButton("Delete selected")
        del_btn.clicked.connect(self._delete)
        bar.addWidget(add_btn)
        bar.addWidget(edit_btn)
        bar.addWidget(del_btn)
        bar.addStretch()
        layout.addLayout(bar)
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Name", "Mode", "Host:Port", "Polling"])
        layout.addWidget(self.table)

    def refresh(self) -> None:
        try:
            devices = self._api.get("/api/config/modbus/devices") or []
        except Exception:
            return
        self.table.setRowCount(len(devices))
        for row, d in enumerate(devices):
            hp = f"{d.get('host')}:{d.get('port')}" if "rtu" not in str(d.get("mode")) else d.get("serial_port")
            self.table.setItem(row, 0, QTableWidgetItem(str(d.get("name", ""))))
            self.table.setItem(row, 1, QTableWidgetItem(str(d.get("mode", ""))))
            self.table.setItem(row, 2, QTableWidgetItem(str(hp)))
            self.table.setItem(row, 3, QTableWidgetItem(str(d.get("enabled", True))))

    def _selected(self) -> dict | None:
        row = self.table.currentRow()
        if row < 0:
            return None
        name = self.table.item(row, 0).text()
        for d in self._api.get("/api/config/modbus/devices") or []:
            if d.get("name") == name:
                return d
        return None

    def _add(self) -> None:
        dlg = DeviceDialog(self._api, None, self)
        if dlg.exec_() != QDialog.Accepted:
            return
        try:
            self._api.post("/api/config/modbus/devices", dlg.body())
            self.refresh()
        except ApiError as exc:
            QMessageBox.warning(self, "Add device", str(exc))

    def _edit(self) -> None:
        dev = self._selected()
        if not dev:
            QMessageBox.information(self, "Edit", "Select a device row first.")
            return
        dlg = DeviceDialog(self._api, dev, self)
        if dlg.exec_() != QDialog.Accepted:
            return
        try:
            self._api.put(
                f"/api/config/modbus/devices/{dev['name']}",
                dlg.body(),
            )
            self.refresh()
        except ApiError as exc:
            QMessageBox.warning(self, "Edit device", str(exc))

    def _delete(self) -> None:
        dev = self._selected()
        if not dev:
            return
        if QMessageBox.question(self, "Delete", f"Delete device {dev['name']}?") != QMessageBox.Yes:
            return
        try:
            self._api.delete(f"/api/config/modbus/devices/{dev['name']}")
            self.refresh()
        except ApiError as exc:
            QMessageBox.warning(self, "Delete", str(exc))
