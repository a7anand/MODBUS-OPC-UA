# Copyright (c) 2026 Aman Anand, M (T&I), Barauni
from __future__ import annotations

from PyQt5.QtWidgets import QGridLayout, QHBoxLayout, QSplitter, QTableWidget, QTableWidgetItem, QVBoxLayout

from app.gui.pages.base import PageBase
from app.gui.widgets import KpiTile, SectionHeader


class DashboardPage(PageBase):
    screen_id = "dashboard"
    breadcrumb = "Dashboard"

    def __init__(self, api, theme, parent=None) -> None:
        super().__init__(api, theme, parent)
        root = QVBoxLayout(self)
        kpi_row = QHBoxLayout()
        self._kpis = {
            "gateway": KpiTile("Gateway Status", theme),
            "uptime": KpiTile("Uptime", theme),
            "devices": KpiTile("Total Devices", theme),
            "connected": KpiTile("Connected Devices", theme),
            "tags": KpiTile("Total Tags", theme),
            "good": KpiTile("GOOD Tags", theme, state="good"),
            "bad": KpiTile("BAD Tags", theme, state="bad"),
            "uncertain": KpiTile("UNCERTAIN Tags", theme, state="warn"),
            "errors": KpiTile("Comm Errors", theme, state="bad"),
        }
        for tile in self._kpis.values():
            kpi_row.addWidget(tile)
        root.addLayout(kpi_row)

        split = QSplitter()
        left = QVBoxLayout()
        lw = PageBase(api, theme)
        ll = QVBoxLayout(lw)
        ll.addWidget(SectionHeader("Device Communication Health", theme))
        self.device_health = QTableWidget(0, 4)
        self.device_health.setHorizontalHeaderLabels(["Device", "Mode", "Endpoint", "Status"])
        self.device_health.horizontalHeader().setStretchLastSection(True)
        ll.addWidget(self.device_health)
        ll.addWidget(SectionHeader("Tag Quality Summary", theme))
        self.quality_summary = QTableWidget(0, 2)
        self.quality_summary.setHorizontalHeaderLabels(["Quality", "Count"])
        ll.addWidget(self.quality_summary)
        split.addWidget(lw)

        right = PageBase(api, theme)
        rl = QVBoxLayout(right)
        rl.addWidget(SectionHeader("Recent Events", theme))
        self.events = QTableWidget(0, 3)
        self.events.setHorizontalHeaderLabels(["Time", "Severity", "Message"])
        self.events.horizontalHeader().setStretchLastSection(True)
        rl.addWidget(self.events)
        rl.addWidget(SectionHeader("Communication Statistics", theme))
        self.comm_stats = QTableWidget(0, 2)
        self.comm_stats.setHorizontalHeaderLabels(["Metric", "Value"])
        rl.addWidget(self.comm_stats)
        split.addWidget(right)
        split.setSizes([500, 500])
        root.addWidget(split, stretch=1)

    def refresh(self) -> None:
        try:
            st = self.api.get("/api/status") or {}
        except Exception as exc:
            self._kpis["gateway"].set_value("OFFLINE", str(exc), state="bad")
            return
        health = st.get("health") or {}
        gw = st.get("gateway") or {}
        uptime = int(health.get("uptime_sec", 0))
        self._kpis["gateway"].set_value("RUNNING", gw.get("name", "Gateway"), state="good")
        self._kpis["uptime"].set_value(f"{uptime // 3600}h {(uptime % 3600) // 60}m", f"{uptime}s", state="accent")

        modbus = st.get("modbus") or self.api.get("/api/modbus/status") or []
        total_dev = len(modbus)
        connected = sum(1 for d in modbus if d.get("connected"))
        self._kpis["devices"].set_value(str(total_dev), "configured")
        self._kpis["connected"].set_value(
            str(connected),
            f"{connected}/{total_dev}",
            state="good" if connected == total_dev and total_dev else "warn",
        )

        tags = self.api.get("/api/tags") or []
        self._kpis["tags"].set_value(str(len(tags)), "live snapshot")
        good = sum(1 for t in tags if str(t.get("quality", "")).upper() == "GOOD")
        bad = sum(1 for t in tags if str(t.get("quality", "")).upper() == "BAD")
        uncertain = len(tags) - good - bad
        self._kpis["good"].set_value(str(good), "", state="good")
        self._kpis["bad"].set_value(str(bad), "", state="bad")
        self._kpis["uncertain"].set_value(str(uncertain), "", state="warn")

        comm = self.api.get("/api/communication?limit=50") or []
        errors = sum(1 for c in comm if str(c.get("result", "")).lower() not in ("ok", "success", ""))
        self._kpis["errors"].set_value(str(errors), "last 50 polls", state="bad" if errors else "good")

        self.device_health.setRowCount(len(modbus))
        for r, d in enumerate(modbus):
            self.device_health.setItem(r, 0, QTableWidgetItem(str(d.get("name", ""))))
            self.device_health.setItem(r, 1, QTableWidgetItem(str(d.get("mode", ""))))
            ep = f"{d.get('host', '')}:{d.get('port', '')}"
            self.device_health.setItem(r, 2, QTableWidgetItem(ep))
            st_txt = "Connected" if d.get("connected") else "Disconnected"
            self.device_health.setItem(r, 3, QTableWidgetItem(st_txt))

        for table, data in (
            (self.quality_summary, [("GOOD", good), ("BAD", bad), ("OTHER", uncertain)]),
            (self.comm_stats, [("Samples", len(comm)), ("Errors", errors)]),
        ):
            table.setRowCount(len(data))
            for r, (a, b) in enumerate(data):
                table.setItem(r, 0, QTableWidgetItem(str(a)))
                table.setItem(r, 1, QTableWidgetItem(str(b)))

        evs = self.api.get("/api/events") or []
        show = evs[:25]
        self.events.setRowCount(len(show))
        for r, e in enumerate(show):
            self.events.setItem(r, 0, QTableWidgetItem(str(e.get("timestamp", ""))))
            self.events.setItem(r, 1, QTableWidgetItem(str(e.get("severity", ""))))
            self.events.setItem(r, 2, QTableWidgetItem(str(e.get("message", ""))))
