# Copyright (c) 2026 Aman Anand, M (T&I), Barauni
"""One-shot Modbus read test — POST /api/modbus/read."""

from __future__ import annotations

from PyQt5.QtWidgets import (
    QComboBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.gui_shared.api_client import ApiError, GatewayApiClient


class ModbusToolPage(QWidget):
    def __init__(self, api: GatewayApiClient, parent=None) -> None:
        super().__init__(parent)
        self._api = api
        layout = QVBoxLayout(self)
        form = QFormLayout()
        self.device = QLineEdit("SIM_PLC")
        self.unit_id = QSpinBox()
        self.unit_id.setRange(0, 247)
        self.unit_id.setValue(1)
        self.area = QComboBox()
        for a in ("holding_register", "input_register", "coil", "discrete_input"):
            self.area.addItem(a)
        self.address = QSpinBox()
        self.address.setRange(0, 65535)
        self.count = QSpinBox()
        self.count.setRange(1, 125)
        self.count.setValue(1)
        form.addRow("Device name", self.device)
        form.addRow("Unit ID", self.unit_id)
        form.addRow("Area", self.area)
        form.addRow("Address (internal/zero)", self.address)
        form.addRow("Count", self.count)
        layout.addLayout(form)
        read_btn = QPushButton("Read")
        read_btn.clicked.connect(self._read)
        layout.addWidget(read_btn)
        self.output = QTextEdit()
        self.output.setReadOnly(True)
        layout.addWidget(self.output)

    def refresh(self) -> None:
        try:
            devices = self._api.get("/api/config/modbus/devices") or []
            if devices and not self.device.text().strip():
                self.device.setText(str(devices[0].get("name", "")))
        except Exception:
            pass

    def _read(self) -> None:
        body = {
            "device": self.device.text().strip(),
            "unit_id": self.unit_id.value(),
            "area": self.area.currentText(),
            "address": self.address.value(),
            "count": self.count.value(),
        }
        try:
            result = self._api.post("/api/modbus/read", body)
            import json

            self.output.setPlainText(json.dumps(result, indent=2))
        except ApiError as exc:
            QMessageBox.warning(self, "Modbus read", str(exc))
