# Copyright (c) 2026 Aman Anand, M (T&I), Barauni
"""Secondary screens — certificates, users, simulators, system diagnostics."""

from __future__ import annotations

import json

from PyQt5.QtWidgets import QLabel, QPlainTextEdit, QVBoxLayout

from app.gui_v2.pages.base import PageBase
from app.gui_v2.widgets import SectionHeader


class _ApiDumpPage(PageBase):
    def __init__(self, api, theme, screen_id: str, breadcrumb: str, path: str, parent=None) -> None:
        super().__init__(api, theme, parent)
        self.screen_id = screen_id
        self.breadcrumb = breadcrumb
        self._path = path
        layout = QVBoxLayout(self)
        layout.addWidget(SectionHeader(breadcrumb, theme))
        self.body = QPlainTextEdit()
        self.body.setReadOnly(True)
        layout.addWidget(self.body)

    def refresh(self) -> None:
        try:
            data = self.api.get(self._path)
            self.body.setPlainText(json.dumps(data, indent=2))
        except Exception as exc:
            self.body.setPlainText(str(exc))


class RegisterViewerPage(PageBase):
    screen_id = "diag_registers"
    breadcrumb = "Diagnostics / Register Viewer"

    def __init__(self, api, theme, parent=None) -> None:
        super().__init__(api, theme, parent)
        self.screen_id = "diag_registers"
        layout = QVBoxLayout(self)
        layout.addWidget(SectionHeader("Register Viewer", theme))
        layout.addWidget(QLabel("Live tag register map — same data as Tag Manager with address focus."))
        self._hint = QLabel("Use Modbus Diagnostic Tool for ad-hoc reads.")
        layout.addWidget(self._hint)

    def refresh(self) -> None:
        pass


def certificates_page(api, theme, parent=None) -> PageBase:
    return _ApiDumpPage(api, theme, "certificates", "Certificates", "/api/certificates", parent)


def users_page(api, theme, parent=None) -> PageBase:
    return _ApiDumpPage(api, theme, "users", "Users & Security", "/api/audit", parent)


def simulators_page(api, theme, parent=None) -> PageBase:
    p = _ApiDumpPage(api, theme, "simulators", "Simulators", "/api/config", parent)
    return p


def system_page(api, theme, parent=None) -> PageBase:
    return _ApiDumpPage(api, theme, "system", "System Diagnostics", "/api/status", parent)
