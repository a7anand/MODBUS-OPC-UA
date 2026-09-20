# Copyright (c) 2026 Aman Anand, M (T&I), Barauni
"""Gateway runtime entry."""

from __future__ import annotations

import asyncio
import logging
import sys
import webbrowser
from pathlib import Path

import uvicorn

from app.api.app import create_app
from app.core.gateway import Gateway
from app.utils.logging_setup import configure_logging as setup_rotating_logs


async def run_gateway_async(
    config_path: Path, portable: bool = False, open_browser: bool = False
) -> int:
    if portable:
        # Portable mode: config/data/logs live beside the executable (see docs/DEPLOYMENT.md).
        pass
    gateway = Gateway(config_path)
    await gateway.load()
    setup_rotating_logs(gateway.doc.logging.level if gateway.doc else "INFO")
    await gateway.start()
    web = gateway.doc.web if gateway.doc else None
    server = None
    if web and web.enabled:
        api = create_app(gateway)
        config = uvicorn.Config(
            api,
            host=web.host,
            port=web.port,
            log_level="warning",
        )
        server = uvicorn.Server(config)
        asyncio.create_task(server.serve())
        if open_browser:
            host = web.host if web.host not in ("0.0.0.0", "::") else "127.0.0.1"
            url = f"http://{host}:{web.port}/"
            loop = asyncio.get_running_loop()
            loop.call_later(2.0, lambda: webbrowser.open(url))
            print(f"Web UI: {url}")
    try:
        await gateway.run_until_stopped()
    except KeyboardInterrupt:
        pass
    finally:
        if server:
            server.should_exit = True
        await gateway.stop()
    return 0


def run_gateway(
    config_path: Path, portable: bool = False, open_browser: bool = False
) -> int:
    try:
        return asyncio.run(
            run_gateway_async(
                config_path, portable=portable, open_browser=open_browser
            )
        )
    except KeyboardInterrupt:
        return 0


def run_gui(config_path: Path) -> int:
    try:
        from app.gui.main_window import run_gui_app
    except ImportError:
        print("PyQt5 not installed. pip install PyQt5 or pip install -e '.[gui]'", file=sys.stderr)
        return 1
    return run_gui_app(config_path)


def run_gui_v1(config_path: Path) -> int:
    try:
        from app.gui_v1.main_window import run_gui_app
    except ImportError:
        print("PyQt5 not installed. pip install PyQt5 or pip install -e '.[gui]'", file=sys.stderr)
        return 1
    return run_gui_app(config_path)


if __name__ == "__main__":
    from app.cli import main

    raise SystemExit(main())
