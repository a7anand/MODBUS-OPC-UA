# Copyright (c) 2026 Aman Anand, M (T&I), Barauni
from __future__ import annotations

import json

from PyQt5.QtWidgets import (
    QLabel,
    QListWidget,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from app.gui.pages.base import PageBase
from app.gui.widgets import SectionHeader
from app.gui_shared.api_client import ApiError


class ConfigWizardPage(PageBase):
    screen_id = "cfg_wizard"
    breadcrumb = "Configuration / Setup Wizard"

    STEPS = [
        "Gateway",
        "Modbus",
        "OPC UA",
        "Tags",
        "Mappings",
        "Validation",
        "Apply",
    ]

    def __init__(self, api, theme, parent=None) -> None:
        super().__init__(api, theme, parent)
        layout = QVBoxLayout(self)
        layout.addWidget(SectionHeader("Configuration Wizard", theme))
        self.steps = QListWidget()
        self.steps.addItems(self.STEPS)
        self.stack = QStackedWidget()
        self._editors: list[QWidget] = []
        for step in self.STEPS:
            w = QLabel(f"Step: {step}\n\nUse dedicated screens to edit {step} settings, then validate here.")
            w.setWordWrap(True)
            self.stack.addWidget(w)
            self._editors.append(w)
        summary = QLabel()
        summary.setWordWrap(True)
        self.stack.addWidget(summary)
        self._summary = summary

        layout.addWidget(self.steps)
        layout.addWidget(self.stack, stretch=1)
        bar = QWidget()
        bl = QVBoxLayout(bar)
        validate_btn = QPushButton("Validate configuration")
        validate_btn.clicked.connect(self._validate)
        apply_btn = QPushButton("Apply (reload gateway)")
        apply_btn.setProperty("class", "primary")
        apply_btn.clicked.connect(self._apply)
        bl.addWidget(validate_btn)
        bl.addWidget(apply_btn)
        layout.addWidget(bar)
        self.steps.currentRowChanged.connect(self.stack.setCurrentIndex)

    def refresh(self) -> None:
        try:
            cfg = self.api.get("/api/config") or {}
            self._summary.setText(
                f"Gateway: {cfg.get('gateway', {}).get('name', '')}\n"
                f"Devices: {len((cfg.get('modbus') or {}).get('devices', []))}\n"
                f"Tags: {len(cfg.get('tags', []))}"
            )
        except Exception:
            pass

    def _validate(self) -> None:
        try:
            cfg = self.api.get("/api/config") or {}
            result = self.api.post("/api/config/validate", cfg)
            if result.get("valid"):
                QMessageBox.information(self, "Validation", "Configuration is valid.")
            else:
                QMessageBox.warning(self, "Validation", result.get("error", "Invalid"))
        except ApiError as exc:
            QMessageBox.warning(self, "Validation", str(exc))

    def _apply(self) -> None:
        try:
            cfg = self.api.get("/api/config") or {}
            self.api.post("/api/config/apply", cfg)
            QMessageBox.information(self, "Apply", "Configuration applied.")
        except ApiError as exc:
            QMessageBox.warning(self, "Apply", str(exc))
