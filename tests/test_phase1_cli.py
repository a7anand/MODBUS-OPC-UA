# Copyright (c) 2026 Aman Anand, M (T&I), Barauni
"""Phase 1 CLI and schema v0 validation."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.cli import main
from app.core.config_manager import ConfigError, ConfigManager

ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "examples" / "gateway.yaml"
CORE_CONFIG = ROOT / "config" / "gateway.core.yaml"


def test_help_exits_zero() -> None:
    with pytest.raises(SystemExit) as exited:
        main(["--help"])
    assert exited.value.code == 0


def test_version_exits_zero() -> None:
    with pytest.raises(SystemExit) as exited:
        main(["--version"])
    assert exited.value.code == 0


def test_default_invocation_prints_help() -> None:
    assert main([]) == 0


def test_validate_example_config() -> None:
    assert main(["--validate", "--config", str(EXAMPLE)]) == 0


def test_validate_core_config() -> None:
    assert main(["--validate", "--config", str(CORE_CONFIG)]) == 0


def test_validate_missing_file() -> None:
    assert main(["--validate", "--config", str(ROOT / "no-such.yaml")]) == 1


def test_reserved_flags_exit_two() -> None:
    assert main(["--simulator"]) == 2
    assert main(["--service"]) == 2
    assert main(["--portable"]) == 2


def test_schema_v0_rejects_remote_bind_without_flag(tmp_path: Path) -> None:
    path = tmp_path / "remote.yaml"
    path.write_text(
        "gateway:\n  name: TEST\nweb:\n  host: 0.0.0.0\n  port: 8080\n",
        encoding="utf-8",
    )
    with pytest.raises(ConfigError):
        ConfigManager().load_and_validate(path)


def test_schema_v0_allows_explicit_remote(tmp_path: Path) -> None:
    path = tmp_path / "remote.yaml"
    path.write_text(
        "gateway:\n  name: TEST\n"
        "web:\n  host: 0.0.0.0\n  port: 8080\n  remote_enabled: true\n",
        encoding="utf-8",
    )
    cfg = ConfigManager().load_and_validate(path)
    assert cfg.web.host == "0.0.0.0"
    assert cfg.web.remote_enabled is True


def test_schema_v0_requires_gateway_name(tmp_path: Path) -> None:
    path = tmp_path / "noname.yaml"
    path.write_text("web:\n  host: 127.0.0.1\n", encoding="utf-8")
    with pytest.raises(ConfigError):
        ConfigManager().load_and_validate(path)
