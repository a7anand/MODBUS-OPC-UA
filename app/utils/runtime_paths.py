# Copyright (c) 2026 Aman Anand, M (T&I), Barauni
"""Paths for dev vs PyInstaller one-file/one-dir executables."""

from __future__ import annotations

import shutil
import sys
from pathlib import Path


def is_frozen() -> bool:
    return bool(getattr(sys, "frozen", False))


def bundle_dir() -> Path:
    """Read-only bundled resources (templates, default config)."""
    if is_frozen():
        return Path(getattr(sys, "_MEIPASS", Path.cwd()))
    return Path(__file__).resolve().parents[2]


def app_root() -> Path:
    """Writable directory: project root in dev, folder containing .exe when frozen."""
    if is_frozen():
        return Path(sys.executable).resolve().parent
    return Path.cwd()


def default_config_path() -> Path:
    return app_root() / "config" / "gateway.yaml"


def ensure_portable_layout() -> Path:
    """Create data/logs next to EXE; seed config from bundle on first run."""
    root = app_root()
    for rel in ("config", "data", "logs", "backup", "certificates/own", "imports"):
        (root / rel).mkdir(parents=True, exist_ok=True)
    cfg = root / "config" / "gateway.yaml"
    bundle = bundle_dir()
    bundled = bundle / "config" / "gateway.yaml"
    portable_template = bundle / "examples" / "gateway.portable-service.yaml"
    if not cfg.exists():
        if portable_template.is_file():
            shutil.copy2(portable_template, cfg)
        elif bundled.is_file():
            shutil.copy2(bundled, cfg)
    examples_src = bundle_dir() / "examples"
    examples_dst = root / "examples"
    if examples_src.is_dir() and not examples_dst.exists():
        shutil.copytree(examples_src, examples_dst)
    return cfg
