# Windows compatibility

**Do not treat any OS as supported until a row in this table is marked Tested.** Untested means the product has not been run on that OS.

## Target tracks

| Track | OS | Status |
|-------|----|--------|
| Modern (primary) | Windows 10, Windows 11, Windows Server 2016+ | In development on Windows 11 x64 |
| Legacy (Phase 30) | Windows 7 SP1, 8, 8.1, Server 2008 R2 SP1, Server 2012 / 2012 R2 | **Untested** — `requirements/legacy.txt` is a stub |

Architecture: x64. 32-bit Windows is not a current target.

## Runtime matrix (modern)

| Component | Selection | Reason | Status |
|-----------|-----------|--------|--------|
| OS | Windows 11 x64 (dev) | Primary engineering machine | In use |
| Python | 3.10–3.12 (dev pin 3.11) | Matches `requires-python`; asyncua/pymodbus 3 need 3.10+ | Untested as packaged product |
| PyQt / Qt | PyQt5 / Qt5 | Master prompt prefers Qt5; PyQt6 is not assumed | Not installed until GUI extra |
| pymodbus | 3.6.x–3.x | Async TCP/RTU client and server | Present in current venv |
| OPC UA | asyncua 1.1–2.x | Client and server, certificates | Present in current venv |
| pyserial | 3.5+ | Modbus RTU | Declared; not exercised |
| FastAPI / Uvicorn | FastAPI 0.115+, Uvicorn 0.30+ | Embedded HTTP/WS, no external web server | Present in current venv |
| PyInstaller | 6.x (optional extra) | Portable EXE without a system Python | Not run (Phase 28) |

## Legacy (untested)

Windows 7 SP1 and Server 2008 R2 typically need Python 3.8 and older wheels. A single modern stack cannot honestly support that matrix. Phase 30 will add a Legacy Build sharing source where practical. Until then:

- Do not ship `requirements/legacy.txt` as a working install
- Do not document Win7/8/2008R2 as supported

## Test log

| Date | OS | Arch | Python | Result | Notes |
|------|----|------|--------|--------|-------|
| 2026-09-20 | Windows 11 | x64 | 3.13 (workspace venv) | pytest 26+ tests, gateway run on 4841 | Portable EXE build script provided |

Fill additional rows after each real run. Empty claims of compatibility are forbidden.
