# Copyright (c) 2026 Aman Anand, M (T&I), Barauni
"""Allow ``python -m app`` to invoke the CLI."""

from __future__ import annotations

from app.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
