# Copyright (c) 2026 Aman Anand, M (T&I), Barauni
"""Sidebar navigation tree — screen id in UserRole."""

from __future__ import annotations

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import QTreeWidget, QTreeWidgetItem

NAV_STRUCTURE: list[tuple[str, list[tuple[str, str]] | None]] = [
    ("DASHBOARD", [("dashboard", "Operations Dashboard")]),
    (
        "CONFIGURATION",
        [
            ("cfg_wizard", "Setup Wizard"),
            ("cfg_gateway", "Gateway"),
            ("cfg_modbus", "Modbus Devices"),
            ("cfg_opcua", "OPC UA"),
            ("cfg_web", "Web Server"),
        ],
    ),
    (
        "TAGS",
        [
            ("tags_manager", "Tag Manager"),
            ("tags_mapping", "Mapping"),
            ("tags_import", "Import / Export"),
        ],
    ),
    (
        "DIAGNOSTICS",
        [
            ("diag_modbus", "Modbus Diagnostic Tool"),
            ("diag_registers", "Register Viewer"),
            ("diag_opcua", "OPC UA Browser"),
            ("diag_comm", "Communication Monitor"),
        ],
    ),
    ("EVENTS & ALARMS", [("events", "Event Log")]),
    ("BACKUP & VERSIONING", [("backup", "Backups & Revisions")]),
    ("SIMULATORS", [("simulators", "Simulators")]),
    ("CERTIFICATES", [("certificates", "Certificates")]),
    ("USERS & SECURITY", [("users", "Users & Security")]),
    ("SYSTEM DIAGNOSTICS", [("system", "System Diagnostics")]),
]


class EngineeringSidebar(QTreeWidget):
    screen_changed = pyqtSignal(str)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setHeaderHidden(True)
        self.setIndentation(14)
        self.setAnimated(False)
        self._screen_items: dict[str, QTreeWidgetItem] = {}
        for group, children in NAV_STRUCTURE:
            if children is None:
                continue
            if len(children) == 1 and group == "DASHBOARD":
                sid, label = children[0]
                item = QTreeWidgetItem([label])
                item.setData(0, Qt.UserRole, sid)
                self.addTopLevelItem(item)
                self._screen_items[sid] = item
                continue
            parent_item = QTreeWidgetItem([group])
            parent_item.setFlags(parent_item.flags() & ~Qt.ItemIsSelectable)
            self.addTopLevelItem(parent_item)
            parent_item.setExpanded(True)
            for sid, label in children:
                child = QTreeWidgetItem([label])
                child.setData(0, Qt.UserRole, sid)
                parent_item.addChild(child)
                self._screen_items[sid] = child
        self.currentItemChanged.connect(self._on_item)

    def select_screen(self, screen_id: str) -> None:
        item = self._screen_items.get(screen_id)
        if item:
            self.setCurrentItem(item)

    def _on_item(self, current: QTreeWidgetItem | None, _previous: QTreeWidgetItem | None) -> None:
        if current is None:
            return
        sid = current.data(0, Qt.UserRole)
        if sid:
            self.screen_changed.emit(sid)
