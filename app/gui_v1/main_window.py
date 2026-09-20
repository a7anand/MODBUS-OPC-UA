# Copyright (c) 2026 Aman Anand, M (T&I), Barauni
"""PyQt5 shell — starts Gateway Core in a background thread, all I/O via REST."""

from __future__ import annotations

import sys
import threading
from pathlib import Path

from app.main import run_gateway


def run_gui_app(config_path: Path) -> int:
    from PyQt5.QtCore import QTimer
    from PyQt5.QtWidgets import (
        QApplication,
        QHBoxLayout,
        QListWidget,
        QMainWindow,
        QStackedWidget,
        QVBoxLayout,
        QWidget,
    )

    from app.gui_shared.api_client import GatewayApiClient, api_base_from_config
    from app.gui_v1.communication_monitor import CommunicationMonitorPage
    from app.gui_v1.dashboard import DashboardPage
    from app.gui_v1.devices_page import DevicesPage
    from app.gui_v1.import_page import ImportPage
    from app.gui_v1.modbus_tool import ModbusToolPage
    from app.gui_v1.opcua_browser import OpcUaBrowserPage
    from app.gui_v1.polling_page import PollingPage
    from app.gui_v1.tag_manager import TagManagerPage

    api = GatewayApiClient(api_base_from_config(config_path))

    class MainWindow(QMainWindow):
        def __init__(self) -> None:
            super().__init__()
            self.setWindowTitle("Modbus OPC UA Gateway — Desktop (v1)")
            self.resize(1100, 720)
            nav = QListWidget()
            labels = [
                "Dashboard",
                "Devices",
                "Tags",
                "Import CSV",
                "Polling",
                "Communication / Traffic",
                "Modbus read test",
                "OPC UA browser",
            ]
            nav.addItems(labels)
            self.stack = QStackedWidget()
            self.pages = [
                DashboardPage(api),
                DevicesPage(api),
                TagManagerPage(api),
                ImportPage(api),
                PollingPage(api),
                CommunicationMonitorPage(api),
                ModbusToolPage(api),
                OpcUaBrowserPage(api),
            ]
            for page in self.pages:
                self.stack.addWidget(page)
            nav.currentRowChanged.connect(self._on_nav)
            nav.setCurrentRow(0)
            root = QWidget()
            layout = QHBoxLayout(root)
            layout.addWidget(nav, 1)
            layout.addWidget(self.stack, 4)
            self.setCentralWidget(root)

            threading.Thread(
                target=lambda: run_gateway(config_path),
                name="gateway-core",
                daemon=True,
            ).start()

            self._timer = QTimer(self)
            self._timer.timeout.connect(self._refresh_current)
            self._timer.start(1000)
            self._on_nav(0)

        def _on_nav(self, index: int) -> None:
            self.stack.setCurrentIndex(index)
            self._refresh_current()

        def _refresh_current(self) -> None:
            page = self.pages[self.stack.currentIndex()]
            if hasattr(page, "refresh"):
                page.refresh()

    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    return app.exec_()
