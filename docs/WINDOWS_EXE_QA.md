# Clean-VM portable EXE QA checklist (3.2+)

Use a **fresh Windows 10/11 VM** without Python installed.

| Step | Pass criteria |
|------|----------------|
| Build | `scripts\build_modern.bat` produces `dist\ModbusOPCUAGateway\ModbusOPCUAGateway.exe` |
| First run | `START_GATEWAY.bat` — Web UI at `http://127.0.0.1:8080`, no console tracebacks |
| Modbus sim | Default `config\gateway.yaml` simulator tags update on dashboard |
| OPC UA | UA Expert connects to `opc.tcp://127.0.0.1:4841/` (anonymous lab mode) |
| Service | `INSTALL_STARTUP_SERVICE.bat` (Admin) — process survives reboot |
| Uninstall | `UNINSTALL_STARTUP_SERVICE.bat` removes auto-start |
| Logs | `logs\` rotates; `data\gateway.db` created |

Record VM image, build date, and tester initials in your release notes. Legacy Win7 QA uses `docs/PHASE30_LEGACY.md`.
