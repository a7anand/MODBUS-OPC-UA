# Changelog

## 3.0.1 (2026-09-21)

- Restore API: auto-backup before restore + `reload_config`
- Certificate self-signed generation (`cryptography`), Web button
- Tag import preview JSON/YAML; poll cycle stats → health
- PDF gap doc (`PDF_REMAINING.md`); acceptance TEST 2 + TEST 7

## 3.0.0 (2026-09-21)

Master PDF completion release. See [docs/V3_ROADMAP.md](docs/V3_ROADMAP.md).

- Admin APIs: users, certificates, simulator signals, comm CSV export, tag JSON/YAML export
- Web pages: mapping, OPC UA, backup, simulator, certificates, users, system
- `OpcUaClientSyncService`, mapping feedback validation, STALE quality, UA subscriptions
- Acceptance/manual tests expanded; Phase 30 modern-only documented
- Default GUI V3 (`app/gui/`); frozen V2 at `app/gui_v2/` (`--gui-v2`)

## 3.0.0-dev

- Wave A: health, poll batching, revision compare, gui_v2 freeze

## 2.0.0 (2026-09-21) — frozen

Baseline documented in [docs/VERSION2_FREEZE.md](docs/VERSION2_FREEZE.md).

- Gateway Core Phases 1–26 (Modbus/OPC UA, Web, REST, WebSocket)
- PyQt v1 (`gui_v1`) and v2 industrial workstation (`gui` → now `gui_v2`)
- Portable EXE scripts, Windows startup helpers, full docs set
- 38+ automated tests with `tests/fixtures/gateway_test.yaml`

## 0.1.0 (2026-09-20)

- Initial greenfield `app/` release
