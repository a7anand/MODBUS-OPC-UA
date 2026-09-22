# Versioning guide — Modbus OPC UA Gateway

This document explains **product releases**, **desktop GUI lines**, **how to run each mode**, and **what features appear in which version**.

**Current product version:** `3.2.1` (`app/version.py`, `python -m app --version`)

**Active development branch:** `Version3`  
**Git tags (milestones):** `v2.0.0`, `v3.0.0`, `v3.0.1`, `v3.2.0`

---

## 1. Two axes: product vs desktop GUI

| Concept | What it means |
|--------|----------------|
| **Product version** | Single gateway engine + Web UI + REST API (e.g. `3.2.0`). One codebase under `app/core`, `app/modbus`, `app/opcua`, `app/api`, `app/web`. |
| **GUI line** | PyQt desktop shell only. Three co-installed lines: **v1**, **v2 (frozen)**, **v3 (default)**. They talk to the same REST API via `app/gui_shared/api_client.py`. |

The **Web UI** always matches the **product version** (no separate “web version”).  
Desktop GUIs differ in layout and maturity; **new GUI work goes only into `app/gui/` (v3)** — see [VERSION2_FREEZE.md](VERSION2_FREEZE.md).

```
                    ┌─────────────────────────────────────┐
                    │  Product 3.2.0 (gateway + web API)   │
                    └─────────────────────────────────────┘
                           ▲           ▲           ▲
                           │           │           │
                    --gui-v1    --gui-v2      --gui (v3)
                    gui_v1/     gui_v2/       gui/
```

---

## 2. Product release history (what each version adds)

Features are **cumulative**: `3.2.0` includes everything from `3.0.1` and `3.0.0` unless noted.

| Tag / version | Focus | Notable features |
|---------------|--------|------------------|
| **0.1.0** | Greenfield | Initial `app/` layout |
| **v2.0.0** | PDF Phases 1–26 baseline | Modbus (4 modes), OPC UA server/client, mapping, poll scheduler, embedded Web (core pages), REST, WebSocket, SQLite, backups, CSV import, portable EXE scripts, docs set, PyQt v1 + v2 industrial shell |
| **v3.0.0** | Master PDF “completion” wave | Poll **batching**, **health** (CPU/RAM/disk), OPC UA **client subscriptions** + `OpcUaClientSyncService`, **STALE** quality, mapping **feedback** warnings, admin APIs (users, certs, simulator, exports), Web pages (mapping, OPC UA, backup, simulator, certificates, users, system), **default PyQt v3** (`app/gui/`), v2 frozen to `app/gui_v2/` |
| **v3.0.1** | Safety + acceptance | `POST /api/restore` with **auto-backup** + reload, **self-signed cert generate**, tag import **preview** JSON/YAML, poll stats → health, acceptance **TEST 2** + **TEST 7** |
| **v3.2.0** | Security + diagnostics + ops docs | OPC UA **Sign/SignAndEncrypt** policy matrix, **server username auth**, **cert rotation**, hierarchical OPC UA **browse + subscribe** (Web + PyQt), Modbus **binary/ASCII** analyzer, comm monitor **pause/resume**, [OPCUA_SECURITY.md](OPCUA_SECURITY.md), [NSSM_SERVICE.md](NSSM_SERVICE.md), [WINDOWS_EXE_QA.md](WINDOWS_EXE_QA.md), [PHASE30_LEGACY.md](PHASE30_LEGACY.md) |

**Planned (not released):** see [PDF_REMAINING.md](PDF_REMAINING.md) and [V3_ROADMAP.md](V3_ROADMAP.md) (e.g. **v3.3.0** — full PyQt spec parity, pytest-qt, Win7 hardware sign-off).

Detail per release: [CHANGELOG.md](../CHANGELOG.md).

---

## 3. How to run (all modes)

### 3.1 Prerequisites (developer machine)

```powershell
cd D:\3. Gateways\OPC-MODBUS
python -m venv .venv
.\.venv\Scripts\pip install -e ".[dev]"
```

Config default: `config\gateway.yaml` (or copy from examples).

### 3.2 Gateway + Web UI (headless server)

Starts Modbus/OPC UA engines, embedded FastAPI on `web.host`:`web.port` (default `127.0.0.1:8080`).

```powershell
python -m app --run --config config\gateway.yaml
```

| Flag | Purpose |
|------|---------|
| `--validate` | Load YAML, validate schema, exit (no run) |
| `--portable` | Use portable folder layout (`config/`, `data/`, `logs/` beside CWD or EXE) |
| `--browser` | Open default browser to dashboard (typical with portable EXE) |
| `--simulator` | Use with `--run` when config enables demo simulators |
| `--service` | With `--run`, Windows service entry (see deployment docs) |
| `--version` | Print `ModbusOPCUAGateway` + product version |

**Portable EXE (no Python installed):** double-click `ModbusOPCUAGateway.exe` or `scripts\portable\START_GATEWAY.bat` — equivalent to `--run --portable --browser`.

### 3.3 PyQt desktop (pick one GUI line)

| Command | GUI package | When to use |
|---------|-------------|-------------|
| `python -m app --gui --config config\gateway.yaml` | `app/gui/` **v3** | **Default** — current engineering workstation; receives new screens |
| `python -m app --gui-v2 --config config\gateway.yaml` | `app/gui_v2/` | **Frozen** industrial UI — regression / baseline only |
| `python -m app --gui-v1 --config config\gateway.yaml` | `app/gui_v1/` | Legacy list-style navigation |

**Note:** PyQt GUIs expect the **REST API** to be reachable (usually run gateway in a second terminal with `--run`, unless your GUI build embeds the server — standard dev is two processes or EXE + GUI).

Typical two-terminal dev:

```powershell
# Terminal 1
python -m app --run --config config\gateway.yaml

# Terminal 2
python -m app --gui --config config\gateway.yaml
```

### 3.4 Web-only operator workflow

No PyQt required. After `--run`, open:

| URL | Purpose |
|-----|---------|
| `http://127.0.0.1:8080/` | Dashboard |
| `/devices`, `/tags`, `/mapping`, `/polling`, `/trends`, `/history` | Configuration & data |
| `/traffic`, `/diagnostics`, `/modbus-diag` | Comm monitor & Modbus analyzer (**3.2+**) |
| `/opcua` | OPC UA browser & subscriptions (**3.2+**) |
| `/backup`, `/certificates`, `/users`, `/simulator`, `/system` | Admin (**3.0+**) |
| `/docs` | OpenAPI |

### 3.5 Tests (by product version)

```powershell
python -m pytest tests -q --ignore=tests/test_integration_opcua.py
```

Acceptance tests: `tests/acceptance/` (TEST 1, 2, 7, etc.). RTU: [MANUAL_TEST_RTU.md](MANUAL_TEST_RTU.md).

### 3.6 Build tracks (Windows)

| Track | Script | OS |
|-------|--------|-----|
| Modern | `scripts\build_modern.bat` | Windows 10/11+ |
| Legacy (documented) | `scripts\build_legacy.bat` | Win7 / Py3.8 — operator-guided, [PHASE30_LEGACY.md](PHASE30_LEGACY.md) |

QA checklist: [WINDOWS_EXE_QA.md](WINDOWS_EXE_QA.md).  
Service install: [NSSM_SERVICE.md](NSSM_SERVICE.md).

---

## 4. Desktop GUI comparison

| Capability | v1 `--gui-v1` | v2 `--gui-v2` (frozen) | v3 `--gui` (default) |
|------------|---------------|-------------------------|----------------------|
| Navigation | Simple lists | Industrial workstation shell | Same shell lineage as v2, **active development** |
| Tag / device CRUD | Yes | Yes | Yes |
| Mapping test read/write | Basic | Yes | Yes |
| Comm monitor | Yes | Yes | Yes |
| Modbus diagnostic tool | Basic | Tabs (partial) | **Binary/ASCII tabs** aligned with API (**3.2+**) |
| OPC UA browser | Limited | Flat list | **Hierarchical browse + subscribe** (**3.2+**) |
| Health in status bar | — | Partial | Yes (**3.0+**) |
| New features | **None** (maintenance) | **Frozen** — critical fixes only | **All new GUI work** |

Shared REST client: `app/gui_shared/api_client.py`.

Design target for v3 long-term: [GUI_V2_DESIGN_SPEC.md](GUI_V2_DESIGN_SPEC.md) (full parity → **v3.3**).

---

## 5. Feature matrix by product version (quick lookup)

| Feature | ≥2.0 | ≥3.0.0 | ≥3.0.1 | ≥3.2.0 |
|---------|------|--------|--------|--------|
| Modbus TCP/RTU client/server + simulator | ✓ | ✓ | ✓ | ✓ |
| OPC UA server + client | ✓ | ✓ | ✓ | ✓ |
| Web dashboard + REST + WebSocket | ✓ | ✓ | ✓ | ✓ |
| SQLite audit / config revisions | ✓ | ✓ | ✓ | ✓ |
| Poll register batching | — | ✓ | ✓ | ✓ |
| Health metrics API | — | ✓ | ✓ | ✓ |
| UA client sync + subscriptions | — | ✓ | ✓ | ✓ |
| Web admin (users, certs, simulator, backup UI) | partial | ✓ | ✓ | ✓ |
| Config restore API + auto-backup | — | — | ✓ | ✓ |
| Cert generate (self-signed) | — | — | ✓ | ✓ |
| Tag import preview JSON/YAML | — | — | ✓ | ✓ |
| OPC UA Sign/Encrypt + server users | — | — | — | ✓ |
| Cert **rotation** (archive old) | — | — | — | ✓ |
| OPC UA hierarchical browse + subscribe UI | — | — | — | ✓ |
| Modbus binary/ASCII analyzer (Web + PyQt v3) | — | — | — | ✓ |
| Comm pause/resume API | — | — | — | ✓ |
| NSSM / EXE QA / legacy build docs | partial | partial | partial | ✓ |

---

## 6. Git, branches, and tags

| Item | Meaning |
|------|---------|
| Branch `Version3` | Main line for product **3.x** |
| Tag `v2.0.0` | Frozen snapshot reference for 2.x GUI + core baseline |
| Tag `v3.0.0`, `v3.0.1`, `v3.2.0` | Released milestones; checkout tag to reproduce that release |

```powershell
git fetch --tags
git checkout v3.2.0   # read-only snapshot of 3.2.0
git checkout Version3 # latest development
```

Do **not** commit runtime artifacts: `data/gateway.db`, `backup/*` (local state).

---

## 7. Configuration vs version

YAML schema evolves with the product. New keys (examples in **3.2.0**):

```yaml
opcua:
  server:
    security_mode: sign_and_encrypt   # none | sign | sign_and_encrypt
    username_password_auth: true
    server_users:
      - username: opcuser
        password: changeme
        admin: false
```

REST/Web users remain under `security.users` (hashed passwords). OPC UA server users are separate — see [OPCUA_SECURITY.md](OPCUA_SECURITY.md).

---

## 8. Related documents

| Document | Contents |
|----------|----------|
| [CHANGELOG.md](../CHANGELOG.md) | Release notes |
| [V3_ROADMAP.md](V3_ROADMAP.md) | 3.x checklist |
| [PDF_REMAINING.md](PDF_REMAINING.md) | Gaps vs master PDF |
| [VERSION2_FREEZE.md](VERSION2_FREEZE.md) | v2 GUI freeze policy |
| [ARCHITECTURE.md](ARCHITECTURE.md) | System design |
| [DEPLOYMENT.md](DEPLOYMENT.md) | Production deployment (if present) |

---

## 9. Cheat sheet (copy/paste)

```powershell
# Version
python -m app --version

# Validate config
python -m app --validate --config config\gateway.yaml

# Production-style run
python -m app --run --config config\gateway.yaml

# Desktop v3 (recommended)
python -m app --gui --config config\gateway.yaml

# Frozen desktop v2
python -m app --gui-v2 --config config\gateway.yaml

# Legacy desktop v1
python -m app --gui-v1 --config config\gateway.yaml

# Tests
python -m pytest tests -q --ignore=tests/test_integration_opcua.py
```

---

*Last updated for product **3.2.0**. Update this file when `app/version.py` or release tags change.*
