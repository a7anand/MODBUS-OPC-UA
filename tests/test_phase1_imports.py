# Copyright (c) 2026 Aman Anand, M (T&I), Barauni
"""Phase 1: package imports and GUI isolation from protocol libraries."""

from __future__ import annotations

import importlib
import pkgutil
from pathlib import Path

import app

ROOT = Path(__file__).resolve().parents[1]


def _iter_module_names(package_name: str) -> list[str]:
    package = importlib.import_module(package_name)
    names = [package_name]
    if not hasattr(package, "__path__"):
        return names
    for module in pkgutil.walk_packages(package.__path__, prefix=f"{package_name}."):
        names.append(module.name)
    return names


def test_app_version_and_product_name() -> None:
    assert app.__version__ == "3.2.0"
    assert app.__product_name__ == "ModbusOPCUAGateway"


def test_import_all_app_subpackages() -> None:
    names = _iter_module_names("app")
    assert "app.cli" in names
    assert "app.core.config_manager" in names
    assert "app.modbus.tcp_client" in names
    assert "app.opcua.server" in names
    for name in names:
        if name.startswith("app.gui.") and name != "app.gui":
            try:
                importlib.import_module(name)
            except ModuleNotFoundError as exc:
                if "PyQt5" in str(exc):
                    continue
                raise
            continue
        importlib.import_module(name)


def test_gui_must_not_import_protocol_libraries() -> None:
    for package in ("app.gui", "app.gui_v1", "app.gui_v2"):
        for name in _iter_module_names(package):
            _assert_gui_module_clean(name)


def _assert_gui_module_clean(name: str) -> None:
    try:
        module = importlib.import_module(name)
    except ModuleNotFoundError as exc:
        if "PyQt5" in str(exc):
            return
        raise
    imported = set(module.__dict__)
    assert "pymodbus" not in imported
    assert "asyncua" not in imported
    assert not any(key.startswith("pymodbus") for key in imported)
    assert not any(key.startswith("asyncua") for key in imported)


def test_runtime_directories_exist() -> None:
    for relative in (
        "app/core",
        "app/modbus",
        "app/opcua",
        "app/api/routes",
        "app/web/static",
        "app/gui",
        "app/gui_v2",
        "config",
        "data",
        "backup",
        "logs",
        "certificates/own",
        "certificates/trusted",
        "certificates/rejected",
        "imports",
        "exports",
        "examples",
        "docs",
        "requirements",
        "scripts",
    ):
        assert (ROOT / relative).exists(), relative
