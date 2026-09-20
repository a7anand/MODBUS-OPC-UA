# Copyright (c) 2026 Aman Anand, M (T&I), Barauni
"""Gateway Core facade."""

from __future__ import annotations

import asyncio
import logging
import sys
from pathlib import Path
from typing import Any

from app.core.audit_manager import AuditManager
from app.core.backup_store import BackupStore
from app.core.config_manager import ConfigManager
from app.core.config_schema import GatewayDocument
from app.core.event_manager import EventManager, EventSeverity
from app.core.health_monitor import HealthMonitor
from app.core.mapping_engine import MappingEngine
from app.core.persistence import SqliteStore
from app.core.scheduler import PollScheduler
from app.core.tag_database import TagDatabase
from app.core.tag_history import TagHistoryBuffer
from app.core.trend_buffer import TrendBuffer
from app.modbus.diagnostics import CommunicationMonitor, ModbusDiagnostics
from app.modbus.factory import build_modbus_engine
from app.opcua.client import OpcUaClientEngine
from app.opcua.server import OpcUaServerEngine
from app.security.authentication import AuthService
from app.security.authorization import AuthorizationService
from app.opcua.certificates import CertificateManager
from app.core.ua_client_sync import OpcUaClientSyncService

logger = logging.getLogger(__name__)


class Gateway:
    def __init__(self, config_path: Path) -> None:
        self.config_path = config_path
        self.config_manager = ConfigManager()
        self.doc: GatewayDocument | None = None
        # Live tag values + optional trend samples for the web UI.
        self.trends = TrendBuffer(maxlen=300)
        self.history = TagHistoryBuffer()
        self.tags = TagDatabase(trends=self.trends, history=self.history)
        self.events = EventManager()
        self.audit = AuditManager()
        self.health = HealthMonitor()
        self.comm_monitor = CommunicationMonitor()
        self.backups = BackupStore()
        self.certs = CertificateManager()
        self.modbus = None
        self.opcua_server: OpcUaServerEngine | None = None
        self.opcua_clients: list[OpcUaClientEngine] = []
        self.scheduler: PollScheduler | None = None
        self.modbus_diag: ModbusDiagnostics | None = None
        self.auth: AuthService | None = None
        self.authz: AuthorizationService | None = None
        self.store = SqliteStore()
        self.events.set_store(self.store)
        self.audit.set_store(self.store)
        self._stop_event = asyncio.Event()
        self.ua_sync: OpcUaClientSyncService | None = None

    async def load(self) -> None:
        # Flow: YAML → validated document → tag DB → Modbus/OPC UA engines → scheduler.
        self.doc = self.config_manager.load_and_validate(self.config_path)
        self.tags.build_from_config(self.doc)
        self.auth = AuthService(self.doc)
        self.authz = AuthorizationService(self.doc)
        intervals = {g.id: g.interval_ms for g in self.doc.poll_groups}
        self.modbus = build_modbus_engine(self.doc)
        mapping = MappingEngine(self.doc, self.tags)
        self.opcua_server = OpcUaServerEngine(self.doc, self.tags)
        self.scheduler = PollScheduler(
            self.tags,
            self.modbus,
            mapping,
            intervals,
            on_comm=self._on_comm,
            on_poll_stats=lambda ms, err, tot: self.health.record_poll_cycle(ms, err, tot),
        )
        self.scheduler.set_opcua(self.opcua_server)
        self.modbus_diag = ModbusDiagnostics(self.modbus, self.comm_monitor)
        self.opcua_clients = [
            OpcUaClientEngine(c) for c in self.doc.opcua.clients if c.enabled
        ]
        self.ua_sync = OpcUaClientSyncService(self)

    def _on_comm(self, **kwargs: Any) -> None:
        """Scheduler callback → communication monitor (diagnostics / traffic pages)."""
        self.comm_monitor.log(
            kwargs.get("protocol", "MODBUS"),
            kwargs.get("device", ""),
            kwargs.get("direction", "RX"),
            kwargs.get("operation", "poll"),
            kwargs.get("address"),
            kwargs.get("value"),
            kwargs.get("ok", True),
            kwargs.get("response_ms", 0.0),
            kwargs.get("error"),
            tag_name=kwargs.get("tag_name", ""),
            tx_hex=kwargs.get("tx_hex", ""),
            rx_hex=kwargs.get("rx_hex", ""),
        )

    async def start(self) -> None:
        if self.doc is None:
            await self.load()
        assert self.doc and self.modbus and self.scheduler and self.opcua_server
        await self.modbus.connect_all()
        try:
            await self.opcua_server.start()
        except OSError as exc:
            self.events.emit(
                f"OPC UA server disabled: {exc}",
                EventSeverity.ERROR,
                "opcua",
            )
            logger.error("OPC UA server not started; Modbus and Web UI continue: %s", exc)
        for client in self.opcua_clients:
            try:
                await client.connect()
            except Exception as exc:  # noqa: BLE001
                self.events.emit(
                    f"OPC UA client {client.config.name} failed: {exc}",
                    EventSeverity.ERROR,
                    "opcua",
                )
        if self.opcua_server:
            loop = asyncio.get_running_loop()
            self.opcua_server.set_opcua_write_sink(self._on_opcua_client_write, loop)
        self.scheduler.start()
        if self.ua_sync:
            await self.ua_sync.start()
        self.events.emit("Gateway started", EventSeverity.INFO, "gateway")
        logger.info("Gateway %s started", self.doc.gateway.name)

    async def _on_opcua_client_write(self, tag_name: str, value: Any) -> None:
        ok = await self.write_tag(tag_name, value, username="opcua")
        if not ok:
            self.events.emit(
                f"OPC UA write to {tag_name} failed (check writable, Modbus area, connection)",
                EventSeverity.WARNING,
                "opcua",
            )
            logger.warning("OPC UA client write failed for tag %s", tag_name)

    async def persist_document(
        self, doc: GatewayDocument, user: str = "api", description: str = "config update"
    ) -> None:
        """Validate, backup, save YAML, reload engines."""
        validated = self.config_manager.validate(doc.model_dump(mode="json"))
        self.config_manager.apply_with_store(
            validated, self.config_path, self.store, user=user, description=description
        )
        self.audit.record(user, "config_persist", description, new_value=str(self.config_path))
        await self.reload_config()

    async def reload_config(self) -> None:
        """Reload YAML and restart protocol engines without stopping the process.

        Used after browser/API config saves (devices, tags, poll intervals).
        """
        if self.ua_sync:
            await self.ua_sync.stop()
        if self.scheduler:
            await self.scheduler.stop()
        if self.opcua_server and self.opcua_server.started:
            await self.opcua_server.stop()
        for client in self.opcua_clients:
            await client.disconnect()
        if self.modbus:
            await self.modbus.disconnect_all()
        await self.load()
        await self.modbus.connect_all()
        try:
            await self.opcua_server.start()
        except OSError as exc:
            self.events.emit(f"OPC UA reload failed: {exc}", EventSeverity.ERROR, "opcua")
        for client in self.opcua_clients:
            try:
                await client.connect()
            except Exception as exc:  # noqa: BLE001
                self.events.emit(f"OPC UA client reload failed: {exc}", EventSeverity.ERROR)
        if self.opcua_server:
            loop = asyncio.get_running_loop()
            self.opcua_server.set_opcua_write_sink(self._on_opcua_client_write, loop)
        self.scheduler.start()
        if self.ua_sync:
            await self.ua_sync.start()
        self.events.emit("Configuration reloaded", EventSeverity.INFO, "gateway")

    async def stop(self) -> None:
        if self.ua_sync:
            await self.ua_sync.stop()
        if self.scheduler:
            await self.scheduler.stop()
        if self.opcua_server:
            await self.opcua_server.stop()
        for client in self.opcua_clients:
            await client.disconnect()
        if self.modbus:
            await self.modbus.disconnect_all()
        self.events.emit("Gateway stopped", EventSeverity.INFO, "gateway")
        self._stop_event.set()

    async def run_until_stopped(self) -> None:
        if sys.platform != "win32":
            import signal

            loop = asyncio.get_running_loop()
            for sig in (signal.SIGINT, signal.SIGTERM):
                loop.add_signal_handler(sig, self._stop_event.set)
        await self._stop_event.wait()

    def status(self) -> dict[str, Any]:
        assert self.doc
        return {
            "gateway": self.doc.gateway.model_dump(),
            "health": self.health.snapshot(),
            "modbus": self.modbus.status() if self.modbus else [],
            "tags_count": len(self.tags.names()),
        }

    async def write_tag(self, name: str, value: Any, username: str = "api") -> bool:
        if self.authz and not self.authz.can_write(username):
            return False
        if not self.scheduler:
            return False
        ok = await self.scheduler.write_tag(name, value, origin=f"write:{username}")
        if ok:
            self.audit.record(username, "tag_write", name, new_value=str(value))
            if self.opcua_server:
                await self.opcua_server.update_from_tag(name)
        return ok
