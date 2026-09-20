# Copyright (c) 2026 Aman Anand, M (T&I), Barauni
"""SQLite persistence for audit, events, and configuration revisions."""

from __future__ import annotations

import json
import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class SqliteStore:
    def __init__(self, db_path: Path | None = None) -> None:
        self.path = db_path or Path("data") / "gateway.db"
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_schema(self) -> None:
        with self._lock, self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS config_revisions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    version INTEGER NOT NULL,
                    timestamp TEXT NOT NULL,
                    username TEXT,
                    description TEXT,
                    checksum TEXT,
                    content TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS audit_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    username TEXT,
                    action TEXT,
                    object_name TEXT,
                    old_value TEXT,
                    new_value TEXT,
                    source TEXT,
                    result TEXT
                );
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    severity TEXT,
                    message TEXT,
                    source TEXT,
                    details TEXT
                );
                """
            )

    def save_config_revision(
        self,
        content: str,
        checksum: str,
        username: str,
        description: str,
    ) -> int:
        ts = datetime.now(timezone.utc).isoformat()
        with self._lock, self._connect() as conn:
            cur = conn.execute("SELECT COALESCE(MAX(version), 0) FROM config_revisions")
            version = int(cur.fetchone()[0]) + 1
            conn.execute(
                """
                INSERT INTO config_revisions
                (version, timestamp, username, description, checksum, content)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (version, ts, username, description, checksum, content),
            )
            conn.commit()
            return version

    def list_config_revisions(self, limit: int = 50) -> list[dict[str, Any]]:
        with self._lock, self._connect() as conn:
            rows = conn.execute(
                """
                SELECT version, timestamp, username, description, checksum
                FROM config_revisions ORDER BY version DESC LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [dict(r) for r in rows]

    def get_config_revision(self, version: int) -> str | None:
        with self._lock, self._connect() as conn:
            row = conn.execute(
                "SELECT content FROM config_revisions WHERE version = ?", (version,)
            ).fetchone()
        return row["content"] if row else None

    def insert_audit(
        self,
        username: str,
        action: str,
        object_name: str,
        old_value: str,
        new_value: str,
        source: str,
        result: str,
    ) -> None:
        ts = datetime.now(timezone.utc).isoformat()
        with self._lock, self._connect() as conn:
            conn.execute(
                """
                INSERT INTO audit_log
                (timestamp, username, action, object_name, old_value, new_value, source, result)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (ts, username, action, object_name, old_value, new_value, source, result),
            )
            conn.commit()

    def list_audit(self, limit: int = 200) -> list[dict[str, Any]]:
        with self._lock, self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM audit_log ORDER BY id DESC LIMIT ?", (limit,)
            ).fetchall()
        return [dict(r) for r in rows]

    def insert_event(
        self,
        severity: str,
        message: str,
        source: str,
        details: dict[str, Any] | None,
    ) -> None:
        ts = datetime.now(timezone.utc).isoformat()
        with self._lock, self._connect() as conn:
            conn.execute(
                """
                INSERT INTO events (timestamp, severity, message, source, details)
                VALUES (?, ?, ?, ?, ?)
                """,
                (ts, severity, message, source, json.dumps(details or {})),
            )
            conn.commit()

    def list_events(self, limit: int = 200) -> list[dict[str, Any]]:
        with self._lock, self._connect() as conn:
            rows = conn.execute(
                "SELECT timestamp, severity, message, source, details FROM events ORDER BY id DESC LIMIT ?",
                (limit,),
            ).fetchall()
        out = []
        for r in rows:
            d = dict(r)
            try:
                d["details"] = json.loads(d.get("details") or "{}")
            except json.JSONDecodeError:
                d["details"] = {}
            out.append(d)
        return out
