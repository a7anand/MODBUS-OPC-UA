# Copyright (c) 2026 Aman Anand, M (T&I), Barauni
from __future__ import annotations

import json

from PyQt5.QtWidgets import QLabel, QPlainTextEdit, QVBoxLayout

from app.gui_v2.pages.base import PageBase
from app.gui_v2.widgets import SectionHeader
from app.gui_v1.devices_page import DevicesPage


class ModbusDevicesPage(PageBase):
    screen_id = "cfg_modbus"
    breadcrumb = "Configuration / Modbus Devices"

    def __init__(self, api, theme, parent=None) -> None:
        super().__init__(api, theme, parent)
        layout = QVBoxLayout(self)
        layout.addWidget(SectionHeader("Modbus Devices", theme))
        self._embed = DevicesPage(api)
        layout.addWidget(self._embed)

    def refresh(self) -> None:
        self._embed.refresh()


class ConfigJsonPage(PageBase):
    def __init__(self, api, theme, section: str, screen_id: str, breadcrumb: str, parent=None) -> None:
        super().__init__(api, theme, parent)
        self.screen_id = screen_id
        self.breadcrumb = breadcrumb
        self._section = section
        layout = QVBoxLayout(self)
        layout.addWidget(SectionHeader(breadcrumb.split("/")[-1].strip(), theme))
        self.hint = QLabel("Read-only preview — use Setup Wizard to apply changes safely.")
        layout.addWidget(self.hint)
        self.editor = QPlainTextEdit()
        layout.addWidget(self.editor)

    def refresh(self) -> None:
        try:
            cfg = self.api.get("/api/config") or {}
            if self._section:
                data = cfg.get(self._section, cfg)
            else:
                data = cfg.get("gateway", {})
            self.editor.setPlainText(json.dumps(data, indent=2))
        except Exception as exc:
            self.editor.setPlainText(str(exc))


def gateway_page(api, theme, parent=None) -> PageBase:
    return ConfigJsonPage(api, theme, "", "cfg_gateway", "Configuration / Gateway", parent)


def opcua_config_page(api, theme, parent=None) -> PageBase:
    return ConfigJsonPage(api, theme, "opcua", "cfg_opcua", "Configuration / OPC UA", parent)


def web_config_page(api, theme, parent=None) -> PageBase:
    return ConfigJsonPage(api, theme, "web", "cfg_web", "Configuration / Web Server", parent)
