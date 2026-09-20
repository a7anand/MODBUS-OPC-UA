# Copyright (c) 2026 Aman Anand, M (T&I), Barauni
"""HTTP client for PyQt — talks to embedded FastAPI only (no pymodbus/asyncua)."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

import yaml


class ApiError(Exception):
    def __init__(self, message: str, status: int = 0) -> None:
        super().__init__(message)
        self.status = status


def api_base_from_config(config_path: Path) -> str:
    try:
        raw = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
        web = raw.get("web") or {}
        host = str(web.get("host", "127.0.0.1"))
        port = int(web.get("port", 8080))
        if host in ("0.0.0.0", "::"):
            host = "127.0.0.1"
        return f"http://{host}:{port}"
    except Exception:
        return "http://127.0.0.1:8080"


class GatewayApiClient:
    def __init__(self, base_url: str) -> None:
        self.base = base_url.rstrip("/")

    def _request(
        self,
        method: str,
        path: str,
        body: dict[str, Any] | None = None,
        timeout: float = 5.0,
    ) -> Any:
        url = self.base + path
        data = None
        headers = {"Accept": "application/json"}
        if body is not None:
            data = json.dumps(body).encode("utf-8")
            headers["Content-Type"] = "application/json"
        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                raw = resp.read().decode("utf-8")
                if not raw:
                    return None
                return json.loads(raw)
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            try:
                detail = json.loads(detail).get("detail", detail)
            except Exception:
                pass
            raise ApiError(str(detail), exc.code) from exc
        except urllib.error.URLError as exc:
            raise ApiError(f"Cannot reach gateway at {self.base}: {exc.reason}") from exc

    def get(self, path: str) -> Any:
        return self._request("GET", path)

    def post(self, path: str, body: dict[str, Any] | None = None) -> Any:
        return self._request("POST", path, body)

    def put(self, path: str, body: dict[str, Any]) -> Any:
        return self._request("PUT", path, body)

    def delete(self, path: str) -> Any:
        return self._request("DELETE", path)
