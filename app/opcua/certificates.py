# Copyright (c) 2026 Aman Anand, M (T&I), Barauni
"""Certificate store listing (own / trusted / rejected)."""

from __future__ import annotations

from pathlib import Path
from typing import Any


class CertificateManager:
    def __init__(self, base_dir: Path | None = None) -> None:
        self.base = base_dir or Path("certificates")

    def list_all(self) -> dict[str, list[dict[str, Any]]]:
        result: dict[str, list[dict[str, Any]]] = {}
        for store in ("own", "trusted", "rejected", "archive"):
            folder = self.base / store
            folder.mkdir(parents=True, exist_ok=True)
            items = []
            for path in folder.iterdir():
                if path.suffix.lower() in (".pem", ".der", ".crt"):
                    items.append(
                        {
                            "file": path.name,
                            "path": str(path),
                            "size": path.stat().st_size,
                            "store": store,
                        }
                    )
            result[store] = items
        return result
