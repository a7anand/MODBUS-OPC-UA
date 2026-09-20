# Copyright (c) 2026 Aman Anand, M (T&I), Barauni
"""Shared GUI utilities (REST client) — no PyQt dependency."""

from app.gui_shared.api_client import ApiError, GatewayApiClient, api_base_from_config

__all__ = ["ApiError", "GatewayApiClient", "api_base_from_config"]
