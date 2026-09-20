# Copyright (c) 2026 Aman Anand, M (T&I), Barauni
"""PDF §46 TEST 7 — backup, modify, restore rollback."""

from __future__ import annotations

import shutil

import pytest

from app.core.config_manager import ConfigManager
from app.core.gateway import Gateway

from tests.test_paths import TEST_GATEWAY_YAML


@pytest.mark.asyncio
async def test_7_restore_roundtrip(tmp_path):
    cfg = tmp_path / "gateway.yaml"
    shutil.copy(TEST_GATEWAY_YAML, cfg)
    gw = Gateway(cfg)
    await gw.load()
    original_name = gw.doc.gateway.name
    backup_path = gw.config_manager.backup_active(cfg, user="test")
    doc = gw.doc.model_copy(deep=True)
    doc.gateway.name = "MODIFIED-FOR-TEST"
    cfg.write_text(
        ConfigManager().validate(doc.model_dump(mode="json")).model_dump_json(),
        encoding="utf-8",
    )
    gw.backups.restore(backup_path, cfg)
    reloaded = ConfigManager().load_and_validate(cfg)
    assert reloaded.gateway.name == original_name
