# Modbus ↔ OPC UA Gateway

**Author:** Aman Anand, M (T&I), Barauni

Industrial gateway: Modbus TCP/RTU (client and server), OPC UA client and server, mapping, embedded Web UI, REST/WebSocket, optional PyQt5 GUI. **Gateway Core** (`app/core`) is the single source of truth.

## Quick start

```bat
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements\dev.txt
pip install -e .
python -m app --validate --config config\gateway.yaml
python -m app --run --config config\gateway.yaml
```

- Web: `http://127.0.0.1:8080`
- OPC UA: `opc.tcp://localhost:4840` (see config)
- API: `/api/status`, `/api/tags`, OpenAPI at `/docs`

GUI (optional): `pip install -e ".[gui]"` then `python -m app --gui --config config\gateway.yaml` (see [docs/DESKTOP_GUI_MANUAL.md](docs/DESKTOP_GUI_MANUAL.md))

## Layout

| Path | Purpose |
|------|---------|
| `app/core/` | Config, tags, mapping, scheduler, gateway facade |
| `app/modbus/` | TCP/RTU client & server, codec, diagnostics |
| `app/opcua/` | Server, client, certificates |
| `app/api/` + `app/web/` | REST, WebSocket, embedded UI |
| `app/gui/` | PyQt5 (no pymodbus/asyncua imports) |
| `gateway/` | Legacy reference poller (use `config/gateway.legacy.yaml`) |

## Docs

- **[docs/COMPLETE_SYSTEM_REFERENCE.md](docs/COMPLETE_SYSTEM_REFERENCE.md)** — full what/why/where/how + **all APIs**
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
- [docs/WEB_UI_MANUAL.md](docs/WEB_UI_MANUAL.md)
- [docs/WINDOWS_STARTUP_SERVICE.md](docs/WINDOWS_STARTUP_SERVICE.md)
- [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)
- [docs/WINDOWS_COMPATIBILITY.md](docs/WINDOWS_COMPATIBILITY.md)

## Tests

```bat
scripts\run_tests.bat
```

Portable EXE: `scripts\build_windows.bat` (requires PyInstaller).
