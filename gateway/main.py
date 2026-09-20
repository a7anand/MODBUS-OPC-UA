# Copyright (c) 2026 Aman Anand, M (T&I), Barauni
"""Gateway entry point."""

from __future__ import annotations

import argparse
import asyncio
import logging
import signal
import sys
from pathlib import Path

import uvicorn

from gateway.config import GatewayConfig, load_config
from gateway.health import create_app
from gateway.modbus_client import ModbusPool
from gateway.opcua_bridge import OpcUaBridge
from gateway.poller import Poller


def _configure_logging(config: GatewayConfig) -> None:
    level = getattr(logging, config.logging.level.upper(), logging.INFO)
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )


async def run_gateway(config_path: Path) -> None:
    config = load_config(config_path)
    _configure_logging(config)

    modbus = ModbusPool(config.modbus_connections)
    opcua = OpcUaBridge(config)
    poller = Poller(config, modbus, opcua)

    async def on_opcua_write(tag_id: str, value) -> None:
        ok = await poller.write_tag(tag_id, value)
        if not ok:
            logging.getLogger(__name__).error("Write failed for tag %s", tag_id)

    opcua.set_write_callback(on_opcua_write)

    await modbus.connect_all()
    await opcua.start()
    await opcua.subscribe_writes(on_opcua_write)
    poller.start()

    health_server = None
    if config.health.enabled:
        app = create_app(poller)
        config_uvicorn = uvicorn.Config(
            app,
            host=config.health.host,
            port=config.health.port,
            log_level="warning",
        )
        health_server = uvicorn.Server(config_uvicorn)
        asyncio.create_task(health_server.serve())

    stop_event = asyncio.Event()

    def _handle_signal(*_args) -> None:
        stop_event.set()

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, _handle_signal)

    logging.getLogger(__name__).info(
        "Gateway running — config=%s tags=%d",
        config_path,
        len(config.tags),
    )
    await stop_event.wait()

    await poller.stop()
    await opcua.stop()
    await modbus.close_all()
    if health_server is not None:
        health_server.should_exit = True


def run_cli(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="AA Modbus ↔ OPC UA Gateway — Aman Anand, M (T&I), Barauni"
    )
    parser.add_argument(
        "-c",
        "--config",
        type=Path,
        default=Path("config/gateway.yaml"),
        help="Path to gateway YAML configuration",
    )
    args = parser.parse_args(argv)
    if not args.config.is_file():
        print(f"Config not found: {args.config}", file=sys.stderr)
        sys.exit(1)
    try:
        asyncio.run(run_gateway(args.config))
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    run_cli()
