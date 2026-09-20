# Copyright (c) 2026 Aman Anand, M (T&I), Barauni
"""Re-export shared REST client (v1 compatibility)."""

from app.gui_shared.api_client import ApiError, GatewayApiClient, api_base_from_config

__all__ = ["ApiError", "GatewayApiClient", "api_base_from_config"]
