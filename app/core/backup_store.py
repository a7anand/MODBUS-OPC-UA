# Copyright (c) 2026 Aman Anand, M (T&I), Barauni
"""Configuration backup listing and restore helpers."""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any


class BackupStore:
    def __init__(self, backup_dir: Path | None = None) -> None:
        self.backup_dir = backup_dir or Path("backup")

    def list_backups(self) -> list[dict[str, Any]]:
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        items: list[dict[str, Any]] = []
        for path in sorted(self.backup_dir.glob("gateway_*.yaml"), reverse=True):
            meta_path = path.with_suffix(".json")
            meta: dict[str, Any] = {}
            if meta_path.is_file():
                meta = json.loads(meta_path.read_text(encoding="utf-8"))
            items.append(
                {
                    "file": path.name,
                    "path": str(path),
                    "meta": meta,
                }
            )
        return items

    def restore(self, backup_file: Path, active_path: Path) -> None:
        if active_path.is_file():
            shutil.copy2(active_path, active_path.with_suffix(".pre_restore.yaml"))
        shutil.copy2(backup_file, active_path)
