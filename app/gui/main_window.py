# Copyright (c) 2026 Aman Anand, M (T&I), Barauni
"""PyQt v2 — industrial engineering workstation shell."""

from __future__ import annotations

import sys
import threading
from pathlib import Path

from app.main import run_gateway


def run_gui_app(config_path: Path) -> int:
    from PyQt5.QtCore import Qt, QTimer
    from PyQt5.QtWidgets import (
        QAction,
        QApplication,
        QDockWidget,
        QHBoxLayout,
        QLabel,
        QMainWindow,
        QStackedWidget,
        QToolBar,
        QVBoxLayout,
        QWidget,
    )

    from app.gui.navigation import EngineeringSidebar
    from app.gui.pages.backup import BackupVersioningPage
    from app.gui.pages.base import PageBase
    from app.gui.pages.comm_monitor import CommunicationMonitorPage
    from app.gui.pages.config_pages import (
        ModbusDevicesPage,
        gateway_page,
        opcua_config_page,
        web_config_page,
    )
    from app.gui.pages.config_wizard import ConfigWizardPage
    from app.gui.pages.dashboard import DashboardPage
    from app.gui.pages.events import EventsAlarmsPage
    from app.gui.pages.import_export import ImportExportPage
    from app.gui.pages.mapping import MappingEditorPage
    from app.gui.pages.modbus_diag import ModbusDiagnosticPage
    from app.gui.pages.opcua_browser import OpcUaBrowserPage
    from app.gui.pages.tag_manager import TagManagerPage
    from app.gui.pages.utilities import (
        RegisterViewerPage,
        certificates_page,
        simulators_page,
        system_page,
        users_page,
    )
    from app.gui.theme import ThemeManager, ThemeId
    from app.gui_shared.api_client import GatewayApiClient, api_base_from_config

    api = GatewayApiClient(api_base_from_config(config_path))
    theme = ThemeManager()

    class MainWindow(QMainWindow):
        def __init__(self) -> None:
            super().__init__()
            self.setWindowTitle("Modbus OPC UA Gateway — Engineering Workstation (v3)")
            self.resize(1400, 860)
            self._pages: dict[str, PageBase] = {}
            self._build_pages()
            self._breadcrumb = QLabel("Dashboard")
            self._status_labels: dict[str, QLabel] = {}

            central = QWidget()
            cl = QHBoxLayout(central)
            cl.setContentsMargins(0, 0, 0, 0)
            self.sidebar = EngineeringSidebar()
            self.sidebar.setMaximumWidth(260)
            self.sidebar.screen_changed.connect(self._show_screen)
            self.stack = QStackedWidget()
            for page in self._pages.values():
                self.stack.addWidget(page)
            cl.addWidget(self.sidebar)
            right = QVBoxLayout()
            right.setContentsMargins(6, 6, 6, 6)
            self._breadcrumb.setStyleSheet("font-weight: 600; padding: 4px 0;")
            right.addWidget(self._breadcrumb)
            right.addWidget(self.stack, stretch=1)
            rw = QWidget()
            rw.setLayout(right)
            cl.addWidget(rw, stretch=1)
            self.setCentralWidget(central)

            self.toolbar = QToolBar("Context")
            self.toolbar.setMovable(False)
            self.addToolBar(self.toolbar)
            theme_act = QAction("Theme: Dark / Light / System", self)
            theme_act.triggered.connect(lambda: theme.cycle_theme(QApplication.instance()))
            self.toolbar.addAction(theme_act)
            self.toolbar.addSeparator()
            refresh_act = QAction("Refresh", self)
            refresh_act.triggered.connect(self._refresh_current)
            self.toolbar.addAction(refresh_act)

            self.detail_dock = QDockWidget("Diagnostic Detail", self)
            self.detail_dock.setVisible(False)
            self.addDockWidget(Qt.RightDockWidgetArea, self.detail_dock)

            sb = self.statusBar()
            for key, text in (
                ("gw", "Gateway: …"),
                ("modbus", "Modbus: …"),
                ("opcua", "OPC UA: …"),
                ("tags", "Tags: …"),
                ("cpu", "CPU: …"),
                ("event", "Last Event: …"),
            ):
                lbl = QLabel(text)
                sb.addPermanentWidget(lbl)
                self._status_labels[key] = lbl

            threading.Thread(
                target=lambda: run_gateway(config_path),
                name="gateway-core",
                daemon=True,
            ).start()

            self._timer = QTimer(self)
            self._timer.timeout.connect(self._tick)
            self._timer.start(1000)

            theme.apply(QApplication.instance())
            self.sidebar.select_screen("dashboard")
            self._show_screen("dashboard")

        def _build_pages(self) -> None:
            factories = [
                DashboardPage,
                ConfigWizardPage,
                lambda a, t, p=None: gateway_page(a, t, p),
                ModbusDevicesPage,
                lambda a, t, p=None: opcua_config_page(a, t, p),
                lambda a, t, p=None: web_config_page(a, t, p),
                TagManagerPage,
                MappingEditorPage,
                ImportExportPage,
                ModbusDiagnosticPage,
                RegisterViewerPage,
                OpcUaBrowserPage,
                CommunicationMonitorPage,
                EventsAlarmsPage,
                BackupVersioningPage,
                simulators_page,
                certificates_page,
                users_page,
                system_page,
            ]
            for factory in factories:
                page = factory(api, theme) if callable(factory) else factory(api, theme)
                self._pages[page.screen_id] = page

        def _show_screen(self, screen_id: str) -> None:
            page = self._pages.get(screen_id)
            if not page:
                return
            self.stack.setCurrentWidget(page)
            self._breadcrumb.setText(page.breadcrumb.replace("/", " › "))
            self.toolbar.clear()
            theme_act = QAction("Theme", self)
            theme_act.triggered.connect(lambda: theme.cycle_theme(QApplication.instance()))
            self.toolbar.addAction(theme_act)
            refresh_act = QAction("Refresh", self)
            refresh_act.triggered.connect(self._refresh_current)
            self.toolbar.addAction(refresh_act)
            for label, slot in page.toolbar_actions():
                act = QAction(label, self)
                act.triggered.connect(slot)
                self.toolbar.addAction(act)
            self._refresh_current()

        def _refresh_current(self) -> None:
            page = self.stack.currentWidget()
            if isinstance(page, PageBase):
                page.refresh()
            self._update_status_bar()

        def _tick(self) -> None:
            self._refresh_current()

        def _update_status_bar(self) -> None:
            try:
                st = api.get("/api/status") or {}
                self._status_labels["gw"].setText("Gateway: RUNNING")
                modbus = st.get("modbus") or api.get("/api/modbus/status") or []
                connected = sum(1 for d in modbus if d.get("connected"))
                self._status_labels["modbus"].setText(f"Modbus: {connected}/{len(modbus)} Connected")
                oua = api.get("/api/opcua/status") or {}
                opc = "Connected" if oua.get("server_running") else "Stopped"
                self._status_labels["opcua"].setText(f"OPC UA: {opc}")
                tags = api.get("/api/tags") or []
                good = sum(1 for t in tags if str(t.get("quality", "")).upper() == "GOOD")
                bad = len(tags) - good
                self._status_labels["tags"].setText(f"Tags: {good} Good / {bad} Bad")
                health = st.get("health") or {}
                mem = health.get("memory_mb")
                cpu = health.get("cpu_percent")
                self._status_labels["cpu"].setText(
                    f"CPU: {cpu}%  Mem: {mem} MB"
                    if mem is not None and cpu is not None
                    else "CPU: —"
                )
                evs = api.get("/api/events") or []
                if evs:
                    self._status_labels["event"].setText(f"Last Event: {evs[0].get('timestamp', '')}")
            except Exception:
                self._status_labels["gw"].setText("Gateway: OFFLINE")

    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    return app.exec_()
