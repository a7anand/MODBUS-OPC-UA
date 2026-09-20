# Copyright (c) 2026 Aman Anand, M (T&I), Barauni
"""Modbus ↔ OPC UA Gateway application package.

Gateway Core is the single source of truth. PyQt and the embedded Web UI are
clients of Core and must not implement protocol I/O themselves.
"""

from __future__ import annotations

__version__ = "0.1.0"
__product_name__ = "ModbusOPCUAGateway"
