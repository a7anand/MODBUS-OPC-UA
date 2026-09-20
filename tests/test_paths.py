# Copyright (c) 2026 Aman Anand, M (T&I), Barauni
"""Shared paths for tests (independent of developer config/gateway.yaml)."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEST_GATEWAY_YAML = ROOT / "tests" / "fixtures" / "gateway_test.yaml"
