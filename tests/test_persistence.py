# Copyright (c) 2026 Aman Anand, M (T&I), Barauni

from pathlib import Path

from app.core.persistence import SqliteStore


def test_sqlite_audit_and_revision(tmp_path: Path):
    db = tmp_path / "t.db"
    store = SqliteStore(db)
    store.insert_audit("u", "test", "obj", "", "x", "api", "OK")
    store.save_config_revision("gateway:\n  name: T\n", "abc", "u", "test")
    assert store.list_audit(10)
    assert store.list_config_revisions(10)
