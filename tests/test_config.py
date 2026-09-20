# Copyright (c) 2026 Aman Anand, M (T&I), Barauni

from pathlib import Path

from app.core.config_manager import ConfigManager
from gateway.config import load_config as load_legacy_config
from tests.test_paths import ROOT, TEST_GATEWAY_YAML


def test_load_app_config():
    cfg = ConfigManager().load_and_validate(TEST_GATEWAY_YAML)
    assert cfg.gateway.name == "BKPL-GATEWAY-01"
    assert cfg.tags[0].address_display is not None


def test_plc_address_mapping():
    cfg = ConfigManager().load_and_validate(TEST_GATEWAY_YAML)
    boiler = next(t for t in cfg.tags if t.name == "boiler_temp")
    assert boiler.address_internal == 0
    assert boiler.address_display == 40001


def test_load_legacy_poller_config():
    cfg = load_legacy_config(ROOT / "config" / "gateway.legacy.yaml")
    assert cfg.tags[0].id == "boiler_temp"
