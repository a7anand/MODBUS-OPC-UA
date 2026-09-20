# Version 3.0 — Master PDF completion roadmap

Tracks remaining items from `Modbus_OPC_UA_Gateway_Master_Development_Prompt.pdf` (Phases 30–32 + §45–46).

**Status key:** `[x]` done in V3 work · `[~]` partial · `[ ]` not started

## V3 entry

- **Version:** `3.0.0-dev` (`app/version.py`)
- **Default GUI:** `python -m app --gui` → `app/gui/` (V3)
- **Frozen V2 GUI:** `--gui-v2` → `app/gui_v2/`

---

## Core & protocols

- [~] Modbus TCP client (full FC 01–16, stats) — V2 baseline; V3: verify FC15/16 paths in all drivers
- [~] Modbus TCP/RTU server — present; V3: acceptance with external master
- [ ] Modbus RTU hardware acceptance (PDF TEST 3) + documented manual test
- [ ] Poll scheduler **register read batching** (`app/core/poll_batch.py`)
- [ ] Mapping **feedback-loop** guards (explicit graph)
- [ ] OPC UA client **subscriptions** + publish → tag DB / Modbus write (`app/opcua/subscriptions.py`)
- [ ] Bidirectional path: external UA → gateway UA client → Modbus (PDF TEST 2)
- [~] OPC UA server security policies beyond None (Sign, certs)
- [ ] STALE quality transitions on timeout

## Health & diagnostics

- [ ] Health: CPU, memory, disk, poll latency (`psutil` in `HealthMonitor`)
- [ ] Expose in `/api/status`, Web system page, PyQt status bar
- [ ] Comm monitor: CSV export, full PDF column parity

## Configuration & data

- [ ] Config revision **compare** API (`GET /api/config/revisions/compare`)
- [ ] JSON/YAML tag import/export (CSV/Excel exist)
- [ ] Restore wizard with auto-backup + diff preview

## Security & certificates

- [ ] Enforce `require_auth` on all mutating routes when enabled
- [ ] Certificate generate/import/trust/reject API + Web + GUI
- [ ] User/role admin UI (Administrator / Engineer / Viewer)

## Simulators (PDF §30)

- [ ] Standard demo tags (PUMP1_SPEED, FLOW, …)
- [ ] Signal modes: manual, random, ramp, sine, toggle, counter

## Web UI (PDF §17 gaps)

- [ ] Mapping editor page
- [ ] OPC UA browser (interactive)
- [ ] Backup/restore
- [ ] Simulator control
- [ ] Certificates
- [ ] Users
- [ ] System diagnostics (health)

## PyQt GUI V3 (`app/gui/`)

- [ ] Complete PDF §14 + `GUI_V2_DESIGN_SPEC.md` (tag manager MV, mapping pipeline, analyzer, etc.)
- [ ] Non-blocking workers for all I/O
- [ ] Practical GUI smoke tests (optional pytest-qt)

## Packaging & platform

- [ ] Phase 30 legacy Windows build (`requirements/legacy.txt`) or document modern-only
- [ ] PyInstaller release tested on clean VM
- [ ] Windows Service (pywin32) optional install path

## Testing (PDF §45–46)

- [x] TEST 1 — sim → OPC UA read (fixture)
- [ ] TEST 2 — UA client → Modbus server
- [ ] TEST 3 — RTU (manual/hardware)
- [~] TEST 4 — device failure
- [ ] TEST 5–6 — Web ↔ PyQt config parity
- [~] TEST 7 — backup rollback verification
- [ ] WebSocket test suite
- [ ] Auth integration tests

---

## V3 implementation waves

| Wave | Focus |
|------|--------|
| **A** (current) | Version freeze, `gui_v2`, health API, poll batching, UA subscriptions skeleton, TEST 2 |
| **B** | Web missing pages, cert/user APIs, simulator signals |
| **C** | PyQt V3 feature-complete vs spec |
| **D** | Legacy build / EXE QA / acceptance 3–7 |

Update this file as items complete.
