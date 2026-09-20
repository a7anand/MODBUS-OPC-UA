# Copyright (c) 2026 Aman Anand, M (T&I), Barauni
"""Background REST calls — keeps UI responsive."""

from __future__ import annotations

from typing import Any, Callable

from PyQt5.QtCore import QObject, QThread, pyqtSignal

from app.gui_shared.api_client import GatewayApiClient


class ApiWorker(QObject):
    finished = pyqtSignal(object)
    failed = pyqtSignal(str)

    def __init__(self, fn: Callable[[], Any]) -> None:
        super().__init__()
        self._fn = fn

    def run(self) -> None:
        try:
            self.finished.emit(self._fn())
        except Exception as exc:  # noqa: BLE001
            self.failed.emit(str(exc))


def run_in_thread(parent: QObject, fn: Callable[[], Any], on_ok: Callable[[Any], None], on_err: Callable[[str], None]) -> QThread:
    thread = QThread(parent)
    worker = ApiWorker(fn)
    worker.moveToThread(thread)
    thread.started.connect(worker.run)
    worker.finished.connect(on_ok)
    worker.failed.connect(on_err)
    worker.finished.connect(thread.quit)
    worker.failed.connect(thread.quit)
    worker.finished.connect(worker.deleteLater)
    worker.failed.connect(worker.deleteLater)
    thread.finished.connect(thread.deleteLater)
    thread.start()
    return thread


class ApiTasks:
    """Convenience wrappers for common gateway API reads."""

    def __init__(self, api: GatewayApiClient) -> None:
        self.api = api

    def fetch_status(self) -> dict[str, Any]:
        return self.api.get("/api/status") or {}

    def fetch_tags(self) -> list[dict[str, Any]]:
        return self.api.get("/api/tags") or []

    def fetch_tag_definitions(self) -> list[dict[str, Any]]:
        return self.api.get("/api/config/tags/definitions") or []

    def fetch_communication(self, limit: int = 200) -> list[dict[str, Any]]:
        return self.api.get(f"/api/communication?limit={limit}") or []

    def fetch_events(self) -> list[dict[str, Any]]:
        return self.api.get("/api/events") or []
