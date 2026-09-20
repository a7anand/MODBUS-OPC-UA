# Copyright (c) 2026 Aman Anand, M (T&I), Barauni
"""CSV tag import — preview + commit (same API as web Import page)."""

from __future__ import annotations

from PyQt5.QtWidgets import (
    QCheckBox,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.gui_shared.api_client import ApiError, GatewayApiClient


class ImportPage(QWidget):
    def __init__(self, api: GatewayApiClient, parent=None) -> None:
        super().__init__(parent)
        self._api = api
        from PyQt5.QtWidgets import QLabel

        layout = QVBoxLayout(self)
        layout.addWidget(
            QLabel("Paste CSV (same columns as examples/tags_import_template.csv), then Preview → Commit.")
        )
        self.csv = QTextEdit()
        layout.addWidget(self.csv)
        self.replace = QCheckBox("Update existing tags with same name")
        layout.addWidget(self.replace)
        preview_btn = QPushButton("Preview import")
        preview_btn.clicked.connect(self._preview)
        layout.addWidget(preview_btn)
        commit_btn = QPushButton("Commit import to gateway")
        commit_btn.clicked.connect(self._commit)
        layout.addWidget(commit_btn)
        self.log = QTextEdit()
        self.log.setReadOnly(True)
        layout.addWidget(self.log)

    def refresh(self) -> None:
        pass

    def _preview(self) -> None:
        try:
            data = self._api.post(
                "/api/config/tags/import/preview",
                {"content": self.csv.toPlainText()},
            )
            lines = [
                f"Rows: {data.get('row_count')} valid: {data.get('valid_tags')}",
                f"Errors: {data.get('errors')}",
                "",
            ]
            for row in data.get("preview") or []:
                lines.append(str(row))
            self.log.setPlainText("\n".join(lines))
        except ApiError as exc:
            QMessageBox.warning(self, "Preview", str(exc))

    def _commit(self) -> None:
        try:
            data = self._api.post(
                "/api/config/tags/import/commit",
                {"replace_existing": self.replace.isChecked()},
            )
            QMessageBox.information(self, "Import", str(data.get("stats", data)))
        except ApiError as exc:
            QMessageBox.warning(self, "Commit", str(exc))
