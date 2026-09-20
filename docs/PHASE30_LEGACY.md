# Phase 30 — Legacy Windows builds

**Status:** Modern-only for Version **3.0.0**.

The master PDF targets Windows 7 / Server 2008 R2. This release line is validated on **Windows 10/11** and **Server 2016+** only.

| Track | Action |
|-------|--------|
| Modern | `pip install -r requirements/modern.txt` · `scripts/build_modern.bat` |
| Legacy | `requirements/legacy.txt` is a **placeholder** — do not ship without a dedicated test matrix |

To pursue legacy support: pin Python 3.8, PyQt5 5.12 wheels, and older pymodbus/asyncua in a separate branch; share `app/` source with modern track.
