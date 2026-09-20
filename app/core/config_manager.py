# Copyright (c) 2026 Aman Anand, M (T&I), Barauni
"""Configuration load, validate, backup, and apply."""

from __future__ import annotations

import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from app.core.persistence import SqliteStore

import yaml

from app.core.config_schema import GatewayDocument


class ConfigError(Exception):
    """Raised when configuration cannot be loaded or validated."""


class ConfigManager:
    def __init__(self, config_dir: Path | None = None, backup_dir: Path | None = None) -> None:
        self.config_dir = config_dir or Path("config")
        self.backup_dir = backup_dir or Path("backup")

    def load_yaml(self, path: Path) -> dict[str, Any]:
        config_path = Path(path)
        if not config_path.is_file():
            raise ConfigError(f"configuration file not found: {config_path}")
        try:
            raw = yaml.safe_load(config_path.read_text(encoding="utf-8"))
        except yaml.YAMLError as exc:
            raise ConfigError(f"invalid YAML in {config_path}: {exc}") from exc
        if raw is None:
            raise ConfigError(f"configuration file is empty: {config_path}")
        if not isinstance(raw, dict):
            raise ConfigError(
                f"configuration root must be a mapping, got {type(raw).__name__}"
            )
        return raw

    def validate(self, data: dict[str, Any]) -> GatewayDocument:
        try:
            return GatewayDocument.model_validate(data)
        except Exception as exc:
            raise ConfigError(str(exc)) from exc

    def load_and_validate(self, path: Path) -> GatewayDocument:
        return self.validate(self.load_yaml(path))

    def checksum(self, data: dict[str, Any]) -> str:
        blob = json.dumps(data, sort_keys=True, default=str).encode("utf-8")
        return hashlib.sha256(blob).hexdigest()

    def backup_active(self, active_path: Path, user: str = "system", description: str = "") -> Path:
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        if not active_path.is_file():
            raise ConfigError(f"no active configuration at {active_path}")
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        dest = self.backup_dir / f"gateway_{ts}.yaml"
        shutil.copy2(active_path, dest)
        meta = {
            "timestamp": ts,
            "user": user,
            "description": description or "automatic backup before apply",
            "source": str(active_path),
            "checksum": self.checksum(self.load_yaml(active_path)),
        }
        dest.with_suffix(".json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
        return dest

    def apply(
        self,
        new_doc: GatewayDocument,
        active_path: Path,
        user: str = "system",
        description: str = "",
    ) -> GatewayDocument:
        """Validate, backup, save. Component restart is handled by Gateway."""
        data = new_doc.model_dump(mode="json")
        self.validate(data)
        if active_path.is_file():
            self.backup_active(active_path, user=user, description=description)
        active_path.parent.mkdir(parents=True, exist_ok=True)
        yaml_text = yaml.safe_dump(data, sort_keys=False, allow_unicode=True)
        active_path.write_text(yaml_text, encoding="utf-8")
        return GatewayDocument.model_validate(data)

    def apply_with_store(
        self,
        new_doc: GatewayDocument,
        active_path: Path,
        store: Any,
        user: str = "system",
        description: str = "",
    ) -> GatewayDocument:
        data = new_doc.model_dump(mode="json")
        validated = self.apply(new_doc, active_path, user=user, description=description)
        if store is not None:
            import yaml as yaml_mod

            store.save_config_revision(
                yaml_mod.safe_dump(data, sort_keys=False, allow_unicode=True),
                self.checksum(data),
                user,
                description or "configuration apply",
            )
        return validated


# Phase 1 alias
GatewayConfig = GatewayDocument
