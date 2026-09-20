# Copyright (c) 2026 Aman Anand, M (T&I), Barauni

from pathlib import Path

from app.core.config_manager import ConfigManager

from tests.test_paths import TEST_GATEWAY_YAML


def test_full_config_loads():
    doc = ConfigManager().load_and_validate(TEST_GATEWAY_YAML)
    assert doc.gateway.name == "BKPL-GATEWAY-01"
    assert len(doc.tags) >= 1
    assert doc.modbus.devices[0].name == "SIM_PLC"


def test_duplicate_tag_rejected(tmp_path):
    path = tmp_path / "bad.yaml"
    path.write_text(
        """
gateway:
  name: X
modbus:
  devices:
    - name: D
      mode: simulator
tags:
  - name: a
    device: D
    function: 3
    address: 40001
  - name: a
    device: D
    function: 3
    address: 40002
""",
        encoding="utf-8",
    )
    try:
        ConfigManager().load_and_validate(path)
        assert False, "expected error"
    except Exception:
        pass
