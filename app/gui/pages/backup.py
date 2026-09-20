# Copyright (c) 2026 Aman Anand, M (T&I), Barauni
from __future__ import annotations

from PyQt5.QtWidgets import QHBoxLayout, QMessageBox, QPushButton, QTableWidget, QTableWidgetItem, QVBoxLayout

from app.gui.pages.base import PageBase
from app.gui.widgets import SectionHeader
from app.gui_shared.api_client import ApiError


class BackupVersioningPage(PageBase):
    screen_id = "backup"
    breadcrumb = "Backup & Versioning"

    def __init__(self, api, theme, parent=None) -> None:
        super().__init__(api, theme, parent)
        layout = QVBoxLayout(self)
        layout.addWidget(SectionHeader("Backups & Config Revisions", theme))
        bar = QHBoxLayout()
        create = QPushButton("Create backup")
        create.clicked.connect(self._backup)
        reload_btn = QPushButton("Reload config")
        reload_btn.clicked.connect(self._reload)
        bar.addWidget(create)
        bar.addWidget(reload_btn)
        bar.addStretch()
        layout.addLayout(bar)
        self.backups = QTableWidget(0, 2)
        self.backups.setHorizontalHeaderLabels(["File", "Created"])
        layout.addWidget(self.backups)
        self.revisions = QTableWidget(0, 2)
        self.revisions.setHorizontalHeaderLabels(["Revision", "User"])
        layout.addWidget(self.revisions)

    def refresh(self) -> None:
        try:
            b = self.api.get("/api/backups") or []
            self.backups.setRowCount(len(b))
            for r, row in enumerate(b):
                self.backups.setItem(r, 0, QTableWidgetItem(str(row.get("file", row))))
                self.backups.setItem(r, 1, QTableWidgetItem(str(row.get("created", ""))))
        except Exception:
            pass
        try:
            revs = self.api.get("/api/config/revisions") or []
            self.revisions.setRowCount(len(revs))
            for r, row in enumerate(revs):
                self.revisions.setItem(r, 0, QTableWidgetItem(str(row.get("id", row))))
                self.revisions.setItem(r, 1, QTableWidgetItem(str(row.get("user", ""))))
        except Exception:
            pass

    def _backup(self) -> None:
        try:
            self.api.post("/api/backups")
            self.refresh()
        except ApiError as exc:
            QMessageBox.warning(self, "Backup", str(exc))

    def _reload(self) -> None:
        try:
            self.api.post("/api/config/reload")
            QMessageBox.information(self, "Reload", "Configuration reloaded.")
        except ApiError as exc:
            QMessageBox.warning(self, "Reload", str(exc))
