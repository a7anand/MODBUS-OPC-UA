# Copyright (c) 2026 Aman Anand, M (T&I), Barauni
"""OPC UA server and tag node management."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable

from asyncua import Server, ua
from gateway.codec import decode_value, encode_value
from gateway.config import GatewayConfig, TagConfig

logger = logging.getLogger(__name__)


@dataclass
class TagRuntime:
    config: TagConfig
    node: Any
    last_value: Any = None
    last_quality: ua.StatusCode = field(
        default_factory=lambda: ua.StatusCode(ua.StatusCodes.Good)
    )
    suppress_write_forward: bool = False


class OpcUaBridge:
    def __init__(self, config: GatewayConfig) -> None:
        self._config = config
        self._server = Server()
        self._tags: dict[str, TagRuntime] = {}
        self._namespace_idx: int = config.opcua.namespace_index
        self._on_write: Callable[[str, Any], None] | None = None

    def set_write_callback(self, cb: Callable[[str, Any], None]) -> None:
        self._on_write = cb

    async def start(self) -> None:
        opc = self._config.opcua
        await self._server.init()
        self._server.set_endpoint(
            f"opc.tcp://{opc.endpoint_host}:{opc.endpoint_port}/"
        )
        self._server.set_server_name(opc.application_name)
        uri = opc.application_uri
        await self._server.set_application_uri(uri)
        self._server.product_uri = opc.product_uri
        self._server.name = opc.application_name

        idx = await self._server.register_namespace(opc.namespace_uri)
        self._namespace_idx = idx

        objects = self._server.nodes.objects
        gateway_obj = await objects.add_object(idx, "Gateway")
        devices: dict[str, Any] = {}

        for tag in self._config.tags:
            device_node = devices.get(tag.device_name)
            if device_node is None:
                device_node = await gateway_obj.add_object(idx, tag.device_name)
                devices[tag.device_name] = device_node

            node_id = self._parse_node_id(tag.opcua_node_id or tag.id, idx)
            var = await device_node.add_variable(
                node_id,
                tag.opcua_browse_name or tag.id,
                self._default_value(tag),
                varianttype=self._variant_type(tag),
            )
            await var.set_writable(tag.writable)
            if tag.description:
                await var.write_attribute(
                    ua.AttributeIds.Description,
                    ua.DataValue(ua.LocalizedText(tag.description)),
                )

            runtime = TagRuntime(config=tag, node=var)
            self._tags[tag.id] = runtime

        await self._server.start()
        logger.info(
            "OPC UA server listening on opc.tcp://%s:%s",
            opc.endpoint_host,
            opc.endpoint_port,
        )

    async def stop(self) -> None:
        await self._server.stop()

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

    def _uses_engineering_real(self, tag: TagConfig) -> bool:
        from gateway.config import DataType

        return tag.data_type in (
            DataType.INT16,
            DataType.UINT16,
            DataType.INT32,
            DataType.UINT32,
        ) and (tag.scale != 1.0 or tag.offset != 0.0)

    def _variant_type(self, tag: TagConfig) -> ua.VariantType:
        from gateway.config import DataType

        if self._uses_engineering_real(tag):
            return ua.VariantType.Float
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
        return mapping[tag.data_type]

    def _coerce_value(self, tag: TagConfig, value: Any) -> Any:
        from gateway.config import DataType

        if self._uses_engineering_real(tag):
            return float(value)
        if tag.data_type == DataType.BOOL:
            return bool(value)
        if tag.data_type in (DataType.INT16, DataType.INT32):
            return int(value)
        if tag.data_type in (DataType.UINT16, DataType.UINT32):
            return int(value)
        if tag.data_type == DataType.FLOAT32:
            return float(value)
        if tag.data_type == DataType.FLOAT64:
            return float(value)
        return value

    def _default_value(self, tag: TagConfig) -> Any:
        from gateway.config import DataType

        if tag.data_type == DataType.BOOL:
            return False
        if tag.data_type == DataType.STRING:
            return ""
        return 0

    async def update_tag(
        self,
        tag_id: str,
        registers: list[int] | None,
        quality: ua.StatusCode,
        raw_value: Any | None = None,
    ) -> None:
        runtime = self._tags.get(tag_id)
        if runtime is None:
            return
        tag = runtime.config
        if quality.is_good() and registers is not None:
            value = decode_value(
                registers,
                tag.data_type,
                tag.byte_order,
                tag.word_order,
                tag.scale,
                tag.offset,
            )
        elif raw_value is not None:
            value = raw_value
        else:
            value = runtime.last_value
        value = self._coerce_value(tag, value)

        if (
            tag.deadband
            and runtime.last_value is not None
            and isinstance(value, (int, float))
            and isinstance(runtime.last_value, (int, float))
            and abs(float(value) - float(runtime.last_value)) < tag.deadband
        ):
            return

        runtime.last_value = value
        runtime.last_quality = quality
        runtime.suppress_write_forward = True
        await runtime.node.write_value(value)
        runtime.suppress_write_forward = False

    async def subscribe_writes(self, handler: Callable[[str, Any], None]) -> None:
        """Forward OPC UA client writes to Modbus for writable tags."""

        writable = [
            (tid, rt) for tid, rt in self._tags.items() if rt.config.writable
        ]
        if not writable:
            return

        class WriteHandler:
            async def datachange_notification(self, node, val, data):  # noqa: N802
                if hasattr(val, "Value"):
                    value = val.Value.Value if hasattr(val.Value, "Value") else val.Value
                else:
                    value = val
                for tag_id, runtime in writable:
                    if runtime.node.nodeid == node.nodeid:
                        if runtime.suppress_write_forward:
                            return
                        result = handler(tag_id, value)
                        if asyncio.iscoroutine(result):
                            await result

        sub = await self._server.create_subscription(200, WriteHandler())
        for _, runtime in writable:
            await sub.subscribe_data_change(runtime.node)

    def registers_for_write(self, tag_id: str, value: Any) -> list[int]:
        tag = self._tags[tag_id].config
        return encode_value(
            value,
            tag.data_type,
            tag.byte_order,
            tag.word_order,
            tag.scale,
            tag.offset,
            tag.length_registers,
        )
