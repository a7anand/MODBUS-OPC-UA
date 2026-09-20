# Version 3.0 — Master PDF completion roadmap

**Release:** `3.0.0` (`app/version.py`)

| GUI | Command |
|-----|---------|
| V3 default | `python -m app --gui` → `app/gui/` |
| V2 frozen | `--gui-v2` → `app/gui_v2/` |
| V1 legacy | `--gui-v1` |

---

## Status (3.0.0)

### Core & protocols
- [x] Poll scheduler register read batching
- [x] Mapping feedback-loop warnings (`mapping_feedback.py`)
- [x] OPC UA client subscriptions + `OpcUaClientSyncService`
- [~] Bidirectional TEST 2 full external UA — partial acceptance test
- [~] Modbus TCP server external master — manual / future harness
- [x] STALE quality after repeated poll failures
- [~] OPC UA Sign/Encrypt — cert stores + import; full policy matrix lab-only

### Health & diagnostics
- [x] CPU / memory / disk in `HealthMonitor`
- [x] `/api/status` + Web `/system` + PyQt status bar
- [x] Comm monitor CSV export API

### Configuration
- [x] Revision compare API
- [x] Tag export JSON/YAML APIs
- [x] Web backup page with compare UI

### Security & certificates
- [x] User admin API + Web `/users`
- [x] Certificate import/trust/reject API + Web `/certificates`
- [~] `require_auth` enforced when enabled (existing `_session` on mutating routes)

### Simulators
- [x] PDF §30 signal modes + Web `/simulator`

### Web UI §17
- [x] Mapping, OPC UA, Backup, Simulator, Certificates, Users, System pages

### PyQt V3
- [~] Industrial shell + health in status bar; full spec parity ongoing

### Packaging
- [x] Phase 30 documented modern-only (`PHASE30_LEGACY.md`)
- [~] EXE QA on clean VM — operator task
- [~] pywin32 service — NSSM path documented

### Testing §45–46
- [x] TEST 1, 4, 5, 6 (partial), 7 list
- [x] TEST 2 partial (UA sync start)
- [x] TEST 3 manual (`MANUAL_TEST_RTU.md`)
- [x] WebSocket route test, auth API smoke, mapping feedback unit test

---

## Post-3.0 (optional)

- Full OPC UA security policy matrix in production configs
- pytest-qt GUI automation
- Legacy Windows build branch
- Register viewer / mapping visual editor depth in PyQt V3
