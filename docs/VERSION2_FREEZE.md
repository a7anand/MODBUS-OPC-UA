# Version 2.0.0 — Frozen baseline

**Frozen:** 2026-09-21  
**Branch tag (recommended):** `v2.0.0` on the commit immediately before Version 3 development  
**Active development:** Version **3.0.0** on branch `Version3`

## What V2 includes

| Layer | Location | Notes |
|-------|----------|--------|
| Gateway Core | `app/core`, `app/modbus`, `app/opcua` | Phases 1–26 per master PDF |
| Web UI | `app/web` | Dashboard, devices, tags, import, trends, history, traffic, polling, events |
| REST + WebSocket | `app/api` | Config CRUD, diagnostics, backups |
| Desktop GUI v1 | `app/gui_v1/` | `--gui-v1` |
| Desktop GUI v2 | `app/gui_v2/` | `--gui-v2` industrial workstation shell |
| Portable EXE | `scripts/package_release.bat` | PyInstaller |
| Docs | `docs/` | Full manual set + `GUI_V2_DESIGN_SPEC.md` |
| Tests | `tests/` + `tests/fixtures/gateway_test.yaml` | 38+ tests (OPC UA integration optional) |

## CLI (V2 product)

```bat
python -m app --run --config config\gateway.yaml
python -m app --gui-v2 --config config\gateway.yaml
python -m app --gui-v1 --config config\gateway.yaml
```

## Do not change V2 GUI code except critical fixes

All new GUI work belongs in **`app/gui/`** (Version 3). Shared REST client: **`app/gui_shared/`**.

## Create git tag (optional)

```powershell
git tag -a v2.0.0 -m "Version 2.0.0 freeze — gateway + web + gui_v2"
```
