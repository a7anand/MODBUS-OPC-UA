# Copyright (c) 2026 Aman Anand, M (T&I), Barauni
from __future__ import annotations

import json

from PyQt5.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QSplitter,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
)

from app.gui.pages.base import PageBase
from app.gui.widgets import SectionHeader
from app.gui_shared.api_client import ApiError


class ModbusDiagnosticPage(PageBase):
    screen_id = "diag_modbus"
    breadcrumb = "Diagnostics / Modbus Diagnostic Tool"

    def __init__(self, api, theme, parent=None) -> None:
        super().__init__(api, theme, parent)
        layout = QVBoxLayout(self)
        layout.addWidget(SectionHeader("Modbus Protocol Analyzer", theme))
        split = QSplitter()

        conn = QGroupBox("Connection")
        cf = QFormLayout(conn)
        self.device = QLineEdit()
        self.unit_id = QSpinBox()
        self.unit_id.setRange(0, 247)
        self.unit_id.setValue(1)
        cf.addRow("Device", self.device)
        cf.addRow("Unit ID", self.unit_id)
        split.addWidget(conn)

        right = PageBase(api, theme)
        rl = QVBoxLayout(right)
        builder = QGroupBox("Request Builder")
        bf = QFormLayout(builder)
        self.area = QComboBox()
        for a in ("holding_register", "input_register", "coil", "discrete_input"):
            self.area.addItem(a)
        self.address = QSpinBox()
        self.address.setRange(0, 65535)
        self.count = QSpinBox()
        self.count.setRange(1, 125)
        self.count.setValue(1)
        bf.addRow("Function area", self.area)
        bf.addRow("Address", self.address)
        bf.addRow("Quantity", self.count)
        rl.addWidget(builder)

        bar = QHBoxLayout()
        send = QPushButton("Send Request")
        send.setProperty("class", "primary")
        send.clicked.connect(self._send)
        self.live_poll = QCheckBox("Live Poll (1s)")
        self.live_poll.toggled.connect(self._toggle_live)
        bar.addWidget(send)
        bar.addWidget(self.live_poll)
        bar.addStretch()
        rl.addLayout(bar)

        self.tabs = QTabWidget()
        self.raw_hex = QTextEdit()
        self.decoded = QTextEdit()
        self.registers = QTextEdit()
        self.bits = QTextEdit()
        self.ascii = QTextEdit()
        self.timing = QTextEdit()
        self.exception = QTextEdit()
        for label, w in (
            ("RAW HEX", self.raw_hex),
            ("DECODED", self.decoded),
            ("REGISTERS", self.registers),
            ("BITS", self.bits),
            ("ASCII", self.ascii),
            ("RESPONSE TIME", self.timing),
            ("EXCEPTION", self.exception),
        ):
            w.setReadOnly(True)
            self.tabs.addTab(w, label)
        rl.addWidget(self.tabs)
        split.addWidget(right)
        split.setSizes([220, 780])
        layout.addWidget(split)
        self._live = False

    def refresh(self) -> None:
        if self._live:
            self._send()
        try:
            devices = self.api.get("/api/config/modbus/devices") or []
            if devices and not self.device.text().strip():
                self.device.setText(str(devices[0].get("name", "")))
        except Exception:
            pass

    def _toggle_live(self, on: bool) -> None:
        self._live = on

    def _send(self) -> None:
        body = {
            "device": self.device.text().strip(),
            "unit_id": self.unit_id.value(),
            "area": self.area.currentText(),
            "address": self.address.value(),
            "count": self.count.value(),
        }
        try:
            result = self.api.post("/api/modbus/read", body)
            text = json.dumps(result, indent=2)
            self.decoded.setPlainText(text)
            self.raw_hex.setPlainText(str(result.get("raw_hex", result.get("hex", ""))))
            self.registers.setPlainText(str(result.get("registers", "")))
            self.timing.setPlainText(str(result.get("response_time_ms", "")))
            self.exception.setPlainText(str(result.get("error", "")))
        except ApiError as exc:
            self.exception.setPlainText(str(exc))
            QMessageBox.warning(self, "Modbus", str(exc))
