# Copyright (c) 2026 Aman Anand, M (T&I), Barauni
"""OPC UA server exposing tags from the tag database."""

from __future__ import annotations

import asyncio
import logging
import re
from collections.abc import Awaitable, Callable
from typing import Any

from asyncua import Server, ua

from app.core.config_schema import GatewayDocument, OpcUaServerConfig
from app.core.enums import DataType, OpcUaSecurityMode, TagQuality
from app.core.tag_database import TagDatabase, TagRecord
from app.opcua.base import OpcUaEndpoint

logger = logging.getLogger(__name__)


class OpcUaServerEngine(OpcUaEndpoint):
    def __init__(self, doc: GatewayDocument, tags: TagDatabase) -> None:
        self._doc = doc
        self._tags = tags
        self._server = Server()
        self._cfg: OpcUaServerConfig = doc.opcua.server
        self._nodes: dict[str, Any] = {}
        self._variant_types: dict[str, ua.VariantType] = {}
        self._namespace_idx = 2
        self._write_sink: Callable[[str, Any], Awaitable[None]] | None = None
        self._loop: asyncio.AbstractEventLoop | None = None
        self._warned_insecure = False
        self._started = False
        self._bound_host = ""
        self._bound_port = 0

    def set_opcua_write_sink(
        self,
        sink: Callable[[str, Any], Awaitable[None]],
        loop: asyncio.AbstractEventLoop | None = None,
    ) -> None:
        """Forward OPC UA client writes (e.g. UA Expert) to Gateway Core → Modbus."""
        self._write_sink = sink
        self._loop = loop or asyncio.get_event_loop()

    def _make_opcua_value_setter(self, tag_name: str):
        def setter(node_data: Any, attr: ua.AttributeIds, datavalue: ua.DataValue) -> None:
            attval = node_data.attributes[attr]
            attval.value = datavalue
            if self._write_sink is None or self._loop is None:
                return
            if datavalue.Value is None or datavalue.Value.Value is None:
                return
            val = datavalue.Value.Value
            self._loop.create_task(self._write_sink(tag_name, val))

        return setter

    def _parse_endpoint(self) -> tuple[str, int]:
        m = re.match(r"opc\.tcp://([^:/]+):(\d+)", self._cfg.endpoint)
        if not m:
            return "127.0.0.1", 4841
        return m.group(1), int(m.group(2))

    def _bind_candidates(self) -> list[tuple[str, int]]:
        host, port = self._parse_endpoint()
        candidates = [(host, port)]
        if (host, port) != ("127.0.0.1", 4841):
            candidates.append(("127.0.0.1", 4841))
        if port == 4840:
            candidates.append((host, 4841))
        # de-dupe preserving order
        seen: set[tuple[str, int]] = set()
        out: list[tuple[str, int]] = []
        for item in candidates:
            if item not in seen:
                seen.add(item)
                out.append(item)
        return out

    async def start(self) -> None:
        if not self._cfg.enabled:
            return
        if self._cfg.security_mode == OpcUaSecurityMode.NONE and not self._warned_insecure:
            logger.warning("OPC UA SecurityPolicy=None — lab use only")
            self._warned_insecure = True
        last_error: OSError | None = None
        for host, port in self._bind_candidates():
            self._server = Server()
            try:
                await self._server.init()
                await self._server.set_application_uri(self._cfg.application_uri)
                self._server.set_endpoint(f"opc.tcp://{host}:{port}/")
                self._server.set_server_name(self._cfg.application_name)
                idx = await self._server.register_namespace(self._cfg.namespace_uri)
                self._namespace_idx = idx
                root = await self._server.nodes.objects.add_object(idx, "Gateway")
                devices: dict[str, Any] = {}
                for rec in self._tags:
                    dev_name = rec.definition.device
                    dev_node = devices.get(dev_name)
                    if dev_node is None:
                        dev_node = await root.add_object(idx, dev_name)
                        devices[dev_name] = dev_node
                    node_id = self._parse_node_id(rec.definition.opcua_node, idx)
                    var = await dev_node.add_variable(
                        node_id,
                        rec.definition.name,
                        self._default_value(rec),
                        varianttype=self._variant_type(rec),
                    )
                    await var.set_writable(rec.definition.writable)
                    if rec.definition.writable:
                        self._server.set_attribute_value_setter(
                            var.nodeid,
                            self._make_opcua_value_setter(rec.definition.name),
                        )
                    vtype = self._variant_type(rec)
                    self._nodes[rec.definition.name] = var
                    self._variant_types[rec.definition.name] = vtype
                    await var.write_value(
                        self._coerce_value(rec, self._default_value(rec)),
                        varianttype=vtype,
                    )
                await self._server.start()
                self._started = True
                self._bound_host, self._bound_port = host, port
                logger.info("OPC UA server at opc.tcp://%s:%s", host, port)
                return
            except OSError as exc:
                last_error = exc
                logger.warning(
                    "OPC UA bind failed on opc.tcp://%s:%s — %s",
                    host,
                    port,
                    exc,
                )
                try:
                    await self._server.stop()
                except Exception:  # noqa: BLE001
                    pass
                self._nodes.clear()
                self._variant_types.clear()
        hint = (
            "Windows may block port 4840 (Hyper-V reserved range). "
            "Set opcua.server.endpoint to opc.tcp://127.0.0.1:4841 in config/gateway.yaml"
        )
        if last_error is not None:
            raise OSError(
                last_error.errno,
                f"{last_error.strerror}. {hint}",
            ) from last_error
        raise OSError("OPC UA server could not bind to any candidate endpoint")

    async def stop(self) -> None:
        if not self._started:
            return
        await self._server.stop()
        self._started = False

    @property
    def started(self) -> bool:
        return self._started

    @property
    def bound_endpoint(self) -> str | None:
        if not self._started:
            return None
        return f"opc.tcp://{self._bound_host}:{self._bound_port}/"

    def _parse_node_id(self, node_id: str, default_idx: int) -> ua.NodeId:
        if node_id.startswith("ns="):
            parts = node_id.split(";", 1)
            ns = int(parts[0].replace("ns=", ""))
            ident = parts[1]
            if ident.startswith("s="):
                return ua.NodeId(ident[2:], ns)
            if ident.startswith("i="):
                return ua.NodeId(int(ident[2:]), ns)
        if node_id.startswith("s="):
            return ua.NodeId(node_id[2:], default_idx)
        return ua.NodeId(node_id, default_idx)

    def _uses_engineering_real(self, rec: TagRecord) -> bool:
        dt = rec.definition.datatype
        return dt in (
            DataType.INT16,
            DataType.UINT16,
            DataType.INT32,
            DataType.UINT32,
        ) and (rec.definition.gain != 1.0 or rec.definition.offset != 0.0)

    def _variant_type(self, rec: TagRecord) -> ua.VariantType:
        if self._uses_engineering_real(rec):
            return ua.VariantType.Float
        dt = rec.definition.datatype
        mapping = {
            DataType.BOOL: ua.VariantType.Boolean,
            DataType.INT16: ua.VariantType.Int16,
            DataType.UINT16: ua.VariantType.UInt16,
            DataType.INT32: ua.VariantType.Int32,
            DataType.UINT32: ua.VariantType.UInt32,
            DataType.FLOAT32: ua.VariantType.Float,
            DataType.FLOAT64: ua.VariantType.Double,
            DataType.STRING: ua.VariantType.String,
        }
        return mapping.get(dt, ua.VariantType.Double)

    def _default_value(self, rec: TagRecord) -> Any:
        if rec.definition.datatype == DataType.BOOL:
            return False
        if rec.definition.datatype == DataType.STRING:
            return ""
        if self._uses_engineering_real(rec):
            return 0.0
        if rec.definition.datatype in (DataType.INT16, DataType.INT32):
            return 0
        return 0.0

    def _coerce_value(self, rec: TagRecord, value: Any) -> Any:
        dt = rec.definition.datatype
        if self._uses_engineering_real(rec):
            return float(value)
        if dt == DataType.BOOL:
            return bool(value)
        if dt in (DataType.INT16, DataType.INT32):
            return int(value)
        if dt in (DataType.UINT16, DataType.UINT32):
            return int(value)
        if dt == DataType.FLOAT32:
            return float(value)
        if dt == DataType.FLOAT64:
            return float(value)
        return value

    async def _write_node_value(self, name: str, rec: TagRecord, value: Any) -> None:
        node = self._nodes.get(name)
        vtype = self._variant_types.get(name)
        if node is None or vtype is None:
            return
        await node.write_value(self._coerce_value(rec, value), varianttype=vtype)

    async def write_node(self, node_id: str, value: Any) -> None:
        for name, node in self._nodes.items():
            if str(node.nodeid) == node_id or name == node_id:
                rec = self._tags.get(name)
                if rec:
                    await self._write_node_value(name, rec, value)
                else:
                    await node.write_value(value)
                return

    async def update_from_tag(self, name: str) -> None:
        if not self._started:
            return
        rec = self._tags.get(name)
        if rec is None or rec.quality != TagQuality.GOOD:
            return
        await self._write_node_value(name, rec, rec.value)

    async def browse(self, node_id: str = "i=85") -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        for name, node in self._nodes.items():
            out.append(
                {
                    "browse_name": name,
                    "node_id": str(node.nodeid),
                    "display_name": name,
                }
            )
        return out
