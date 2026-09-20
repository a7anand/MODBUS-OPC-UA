# Copyright (c) 2026 Aman Anand, M (T&I), Barauni
"""Windows service entry (NSSM or pywin32 wrapper)."""

from __future__ import annotations

import sys
from pathlib import Path


def run_service(config_path: Path) -> int:
    """Run gateway as a long-lived process suitable for NSSM/service wrapper."""
    try:
        import servicemanager  # type: ignore[import-untyped]
        import win32serviceutil  # type: ignore[import-untyped]
    except ImportError:
        print(
            "Windows service mode: install pywin32 or register with NSSM:\n"
            "  nssm install ModbusOpcUaGateway python -m app --run --config config\\gateway.yaml",
            file=sys.stderr,
        )
        from app.main import run_gateway

        return run_gateway(config_path, portable=True)
    # Full pywin32 service class can be added in a later packaging pass.
    from app.main import run_gateway

    return run_gateway(config_path, portable=True)
