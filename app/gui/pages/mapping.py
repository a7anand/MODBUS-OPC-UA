# Copyright (c) 2026 Aman Anand, M (T&I), Barauni
from __future__ import annotations

from PyQt5.QtWidgets import (
    QComboBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.gui.pages.base import PageBase
from app.gui.widgets import SectionHeader
from app.gui_shared.api_client import ApiError


class MappingEditorPage(PageBase):
    screen_id = "tags_mapping"
    breadcrumb = "Tags / Mapping"

    def __init__(self, api, theme, parent=None) -> None:
        super().__init__(api, theme, parent)
        layout = QVBoxLayout(self)
        layout.addWidget(SectionHeader("Mapping Pipeline", theme))

        pipe = QHBoxLayout()
        self.source = self._panel("SOURCE", [
            ("Device", QLineEdit()),
            ("Register", QLineEdit("40001")),
            ("Data type", QComboBox()),
            ("Byte order", QComboBox()),
        ])
        self.source_fields = self.source[1]
        self.source_fields["Data type"].addItems(["UINT16", "INT16", "FLOAT32", "BOOL"])
        self.source_fields["Byte order"].addItems(["ABCD", "CDAB", "BADC", "DCBA"])

        mid = QVBoxLayout()
        mid.addStretch()
        for label in ("Conversion", "Scaling", "Quality"):
            mid.addWidget(QLabel(f"↓ {label}"))
        mid.addStretch()
        mid_w = PageBase(api, theme)
        mid_w.setLayout(mid)

        self.dest = self._panel("DESTINATION", [
            ("Tag name", QLineEdit()),
            ("OPC UA NodeId", QLineEdit()),
            ("Gain", QLineEdit("1.0")),
            ("Offset", QLineEdit("0.0")),
        ])
        self.dest_fields = self.dest[1]

        pipe.addWidget(self.source[0], stretch=1)
        pipe.addWidget(mid_w)
        pipe.addWidget(self.dest[0], stretch=1)
        layout.addLayout(pipe)

        actions = QHBoxLayout()
        test_btn = QPushButton("Read test")
        test_btn.clicked.connect(self._read_test)
        write_btn = QPushButton("Write test")
        write_btn.clicked.connect(self._write_test)
        actions.addWidget(test_btn)
        actions.addWidget(write_btn)
        actions.addStretch()
        layout.addLayout(actions)

        self.validation = QLabel("Select a tag in Tag Manager or enter mapping fields to validate.")
        layout.addWidget(self.validation)

    def _panel(self, title: str, fields: list[tuple[str, QWidget]]) -> tuple[QGroupBox, dict[str, QWidget]]:
        box = QGroupBox(title)
        form = QFormLayout(box)
        mapping: dict[str, QWidget] = {}
        for label, widget in fields:
            form.addRow(label, widget)
            mapping[label] = widget
        return box, mapping

    def refresh(self) -> None:
        pass

    def _read_test(self) -> None:
        tag = self.dest_fields["Tag name"].text().strip()
        if not tag:
            QMessageBox.information(self, "Mapping", "Enter a tag name for read test.")
            return
        try:
            rec = self.api.get(f"/api/tags/{tag}")
            self.validation.setText(f"Live: {rec.get('value')} quality={rec.get('quality')}")
        except ApiError as exc:
            self.validation.setText(str(exc))

    def _write_test(self) -> None:
        QMessageBox.information(
            self,
            "Write test",
            "Use OPC UA Browser or API write after enabling writable on the tag definition.",
        )
