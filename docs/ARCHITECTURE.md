# Architecture

Industrial Modbus ↔ OPC UA Gateway. Gateway Core is the only place that owns tag state, configuration, mapping, quality, health, and audit. PyQt5 and the embedded Web UI are clients of Core.

## Process layout

One OS process, three faces, one core:

- **Faces:** PyQt5 desktop GUI, embedded Web UI, CLI / Windows Service
- **Core:** configuration, tag database, mapping, scheduler, quality, events, audit, health, REST, WebSocket
- **Engines:** Modbus (TCP/RTU client and server), OPC UA (client and server)

GUI and Web never import pymodbus or asyncua. Protocol I/O runs on an asyncio loop. Qt stays on the GUI thread. One failed device must not stop other devices, the Web UI, or the OPC UA server.

## Package map

| Path | Role |
|------|------|
| `app/cli.py` | `--help`, `--version`, `--config`, `--validate` |
| `app/core/` | Single source of truth |
| `app/modbus/` | Shared Modbus engine |
| `app/opcua/` | Shared OPC UA engine |
| `app/api/` | REST and WebSocket over Core |
| `app/web/` | Local templates and static assets (no CDN) |
| `app/gui/` | PyQt5 Model/View clients of Core |
| `app/simulator/` | Built-in test servers (Phase 26) |
| `app/security/` | Authn/z enforced server-side |

The older `gateway/` package is a reference poller (Modbus client → OPC UA server). Do not grow it.

## Tag model (target)

Each tag holds name, description, datatype, value, quality, timestamps, source device/protocol, Modbus mapping (unit, function, display address, internal address, address base, register count), OPC UA node, direction, scaling, engineering unit, enabled, poll interval, and last-write origin.

Addressing never silently adds or subtracts one. Byte/word order is explicit (`ABCD`, `BADC`, `CDAB`, `DCBA`).

## Mapping

Directions: Modbus → OPC UA, OPC UA → Modbus, bidirectional. Conversion, scaling, clamp, deadband, quality propagation. Bidirectional maps ignore echoes using origin tokens.

## Configuration

YAML on disk; Pydantic is the schema. Apply pipeline: validate → report errors → backup active → save → restart affected components → health check → audit.

Schema **v0** (Phase 1): `gateway.name`, `gateway.mode`, `web.enabled`, `web.host`, `web.port`, `web.remote_enabled`. Other keys are ignored until later phases.

Default web bind is `127.0.0.1:8080`. Non-loopback bind requires `web.remote_enabled: true`.

## Concurrency

- Headless CLI/service: asyncio loop on the main thread
- GUI: Core loop in a worker thread; Qt signals and thread-safe queues
- Never one thread per tag; poll groups and batched consecutive registers

## Security

Roles: Administrator, Engineer, Operator, Viewer — enforced in Core/API. Passwords never logged. Certificate stores: `certificates/own`, `trusted`, `rejected`. OPC UA `SecurityPolicy=None` is lab-only and must raise a warning event.

## Persistence

SQLite for configuration revisions, audit, events, users, and coarse statistics. Not a high-frequency historian. Rotating files under `logs/`.

## Stack (modern track)

Python 3.10–3.12, PyQt5, pymodbus 3.x, pyserial, asyncua, PyYAML, Pydantic v2, FastAPI, Uvicorn, Jinja2, PyInstaller (Phase 28).

No Tkinter, Node.js, IIS/Apache/Nginx, external database server, CDN, or cloud license.

## Roadmap status

| Phases | Status |
|--------|--------|
| 1–19 | Core, engines, REST, Web UI, PyQt shell |
| 20–26 | Diagnostics API, import/export, backup, auth, certs, simulators |
| 27 | pytest + `tests/acceptance/` |
| 28–29 | PyInstaller spec, package_release.bat, service/NSSM docs |
| 30 | Legacy requirements stub (untested) |
| 31 | Documentation set under `docs/` |
| 32 | Acceptance tests in `tests/acceptance/test_acceptance.py` |
