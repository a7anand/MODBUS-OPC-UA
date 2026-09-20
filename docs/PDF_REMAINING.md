# Remaining vs master PDF (`Modbus_OPC_UA_Gateway_Master_Development_Prompt.pdf`)

**Reference:** 21-page master prompt · Phases 1–32 · §45–46 acceptance tests.

## Completed in 3.0.x (summary)

Gateway Core SSOT, four Modbus modes, OPC UA server/client, mapping/scaling/quality, poll groups + batching, REST + WebSocket, embedded Web (§17 pages), PyQt v1/v2/v3 shells, SQLite audit/revisions, backups, CSV/Excel import, portable EXE scripts, simulators + signal modes, certs/users admin APIs, health metrics, 44+ tests.

---

## Still open or partial (honest matrix)

| PDF area | Gap | Target version |
|----------|-----|----------------|
| §8–9 OPC UA | Sign/Encrypt matrix, server user auth, cert rotation | 3.2.0 ✓ |
| §12 Mapping | Visual editor + **automated feedback graph** beyond warnings | 3.2 GUI |
| §13 Polling | **Priority** queues, per-device stats in UI | 3.1 ✓ partial stats |
| §20 Modbus diag | Binary/ASCII decode tabs Web + PyQt | 3.2.0 ✓ |
| §21 OPC UA browser | Hierarchical browse + subscribe Web + PyQt | 3.2.0 ✓ |
| §22 Comm monitor | Pause/filter/export in PyQt parity | 3.1 ✓ API export |
| §25 Backup | **Restore + auto-backup + reload** in one API | 3.0.1 ✓ |
| §26 Import | **JSON/YAML import** commit path | 3.0.1 ✓ |
| §27 Auth | **require_auth** on all mutating routes consistently | 3.0.1 ✓ |
| §29 Certs | **Generate** self-signed (not only import) | 3.0.1 ✓ |
| §30 Simulators | OPC UA test server separate process | 3.2 |
| §32 Health | Poll latency wired to health API | 3.0.1 ✓ |
| §34–39 Windows | Legacy Win7 doc, NSSM service, clean-VM EXE QA checklist | 3.2.0 docs ✓ |
| §45 Testing | **TEST 2** (UA client → tag / ua_to_mb) | 3.0.1 ✓ |
| §45 Testing | TEST 2 with external Modbus TCP server read | 3.2 optional |
| §45 Testing | **TEST 3** RTU | manual `MANUAL_TEST_RTU.md` |
| §45–46 | **TEST 5–7** Web↔PyQt parity, rollback proof | 3.1 partial |
| §14–15 PyQt | Full `GUI_V2_DESIGN_SPEC` (frozen cols, bulk edit, wizards) | 3.2–3.3 |
| §45 | pytest-qt, WebSocket live message test | 3.2 |
| Phase 30 | Legacy `requirements/legacy.txt` build | branch only |

---

## Version progression

| Tag | Focus |
|-----|--------|
| **v3.0.0** | Waves A–E baseline |
| **v3.0.1** | Restore, cert generate, JSON/YAML import, health poll stats, TEST 2 + TEST 7 |
| **v3.1.0** | Priority poll queues, PyQt comm monitor parity |
| **v3.2.0** | OPC UA security, browse/subscribe, Modbus analyzer, deployment docs |
| **v3.3.0** | Full PyQt spec parity, pytest-qt, legacy HW sign-off |

Update this file when closing items.
