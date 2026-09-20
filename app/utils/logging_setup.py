# Copyright (c) 2026 Aman Anand, M (T&I), Barauni
"""Rotating log files under logs/."""

from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

LOG_FILES = (
    "gateway.log",
    "modbus.log",
    "opcua.log",
    "web.log",
    "audit.log",
    "error.log",
)

LOGGER_MAP = {
    "app.modbus": "modbus.log",
    "app.opcua": "opcua.log",
    "app.api": "web.log",
    "app.core.audit_manager": "audit.log",
}


def configure_logging(level: str = "INFO", log_dir: Path | None = None) -> None:
    log_path = log_dir or Path("logs")
    log_path.mkdir(parents=True, exist_ok=True)
    root_level = getattr(logging, level.upper(), logging.INFO)
    logging.basicConfig(
        level=root_level,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
        force=True,
    )
    fmt = logging.Formatter("%(asctime)s %(levelname)s [%(name)s] %(message)s")
    gateway_log = log_path / "gateway.log"
    handler = RotatingFileHandler(
        gateway_log, maxBytes=5_000_000, backupCount=5, encoding="utf-8"
    )
    handler.setFormatter(fmt)
    logging.getLogger().addHandler(handler)
    err_handler = RotatingFileHandler(
        log_path / "error.log", maxBytes=2_000_000, backupCount=3, encoding="utf-8"
    )
    err_handler.setLevel(logging.ERROR)
    err_handler.setFormatter(fmt)
    logging.getLogger().addHandler(err_handler)
    for logger_name, filename in LOGGER_MAP.items():
        fh = RotatingFileHandler(
            log_path / filename, maxBytes=2_000_000, backupCount=3, encoding="utf-8"
        )
        fh.setFormatter(fmt)
        logging.getLogger(logger_name).addHandler(fh)
    logging.getLogger("asyncua.server.address_space").setLevel(logging.WARNING)
