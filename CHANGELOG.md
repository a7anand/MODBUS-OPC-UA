# Changelog

## 3.0.0-dev (in progress)

Version 3 completes remaining master-PDF items. See [docs/V3_ROADMAP.md](docs/V3_ROADMAP.md).

- Product version `3.0.0-dev`; default GUI is V3 (`app/gui/`)
- Frozen V2 GUI copied to `app/gui_v2/` (`--gui-v2`)
- Health monitor: CPU / memory / disk via `psutil`
- Modbus poll **register batching** (`app/core/poll_batch.py`)
- OPC UA client subscription manager (`app/opcua/subscriptions.py`)
- Config revision **compare** API (`GET /api/config/revisions/compare`)

## 2.0.0 (2026-09-21) — frozen

Baseline documented in [docs/VERSION2_FREEZE.md](docs/VERSION2_FREEZE.md).

- Gateway Core Phases 1–26 (Modbus/OPC UA, Web, REST, WebSocket)
- PyQt v1 (`gui_v1`) and v2 industrial workstation (`gui` → now `gui_v2`)
- Portable EXE scripts, Windows startup helpers, full docs set
- 38+ automated tests with `tests/fixtures/gateway_test.yaml`

## 0.1.0 (2026-09-20)

- Initial greenfield `app/` release
