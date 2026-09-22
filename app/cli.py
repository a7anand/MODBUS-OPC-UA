# Copyright (c) 2026 Aman Anand, M (T&I), Barauni
"""Command-line interface."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from app import __product_name__, __version__
from app.core.config_manager import ConfigError, ConfigManager
from app.utils.runtime_paths import (
    app_root,
    default_config_path,
    ensure_portable_layout,
    is_frozen,
)


def _default_config_path() -> Path:
    return default_config_path() if is_frozen() else Path("config") / "gateway.yaml"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="modbus-opcua-gateway",
        description=f"{__product_name__} — industrial Modbus ↔ OPC UA gateway.",
    )
    parser.add_argument("--version", action="version", version=f"{__product_name__} {__version__}")
    parser.add_argument(
        "--config",
        type=Path,
        default=_default_config_path(),
        help="Path to YAML configuration",
    )
    parser.add_argument("--validate", action="store_true", help="Validate configuration and exit")
    parser.add_argument("--run", action="store_true", help="Run gateway (headless)")
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Background gateway + Web UI (no PyQt, no browser): --run --portable",
    )
    parser.add_argument(
        "--gui",
        action="store_true",
        help="Run PyQt v3 engineering workstation GUI (default)",
    )
    parser.add_argument(
        "--gui-v2",
        action="store_true",
        help="Run frozen PyQt v2 GUI (see docs/VERSION2_FREEZE.md)",
    )
    parser.add_argument(
        "--gui-v1",
        action="store_true",
        help="Run legacy PyQt v1 list-navigation GUI",
    )
    parser.add_argument("--portable", action="store_true", help="Portable directory layout")
    parser.add_argument("--service", action="store_true", help="Windows service mode")
    parser.add_argument("--simulator", action="store_true", help="Enable demo simulators in config")
    parser.add_argument(
        "--browser",
        action="store_true",
        help="Open default web browser to the dashboard",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    # Double-click portable EXE: run gateway + web UI beside the executable.
    if argv is None and is_frozen() and len(sys.argv) <= 1:
        argv = ["--headless"]
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.headless:
        args.run = True
        args.portable = True
        args.browser = False
    if is_frozen():
        os.chdir(app_root())
    if args.portable or (is_frozen() and args.run):
        seeded = ensure_portable_layout()
        default_rel = Path("config") / "gateway.yaml"
        if args.config in (default_rel, Path("config/gateway.yaml")):
            args.config = seeded
    manager = ConfigManager()

    if args.validate:
        try:
            cfg = manager.load_and_validate(args.config)
        except ConfigError as exc:
            print(f"Configuration invalid: {exc}", file=sys.stderr)
            return 1
        print(f"Configuration valid: {args.config}")
        print(f"  gateway.name = {cfg.gateway.name}")
        print(f"  tags = {len(cfg.tags)}")
        print(f"  modbus devices = {len(cfg.modbus.devices)}")
        print(f"  web = {cfg.web.host}:{cfg.web.port}")
        return 0

    if args.service and not args.run:
        print("Use --service with --run, or register via NSSM (see docs/DEPLOYMENT.md).", file=sys.stderr)
        return 2

    if args.service:
        from app.service.windows_service import run_service

        return run_service(args.config)

    if args.gui_v1:
        from app.main import run_gui_v1

        return run_gui_v1(args.config)

    if args.gui_v2:
        from app.main import run_gui_v2

        return run_gui_v2(args.config)

    if args.gui:
        from app.main import run_gui

        return run_gui(args.config)

    if args.simulator and not args.run:
        print("Use --run --simulator to start the gateway with simulators.", file=sys.stderr)
        return 2

    if args.portable and not args.run:
        print("Use --run --portable for portable layout.", file=sys.stderr)
        return 2

    if args.run or args.portable:
        from app.main import run_gateway

        return run_gateway(
            args.config, portable=args.portable, open_browser=args.browser
        )

    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
