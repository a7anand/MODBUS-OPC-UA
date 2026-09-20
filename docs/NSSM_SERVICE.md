# Windows service via NSSM (PDF §34–39)

The gateway portable folder includes `scripts/portable/INSTALL_STARTUP_SERVICE.bat`, which calls `scripts/windows/Install-GatewayStartup.ps1`.

## Preferred: NSSM

1. Download [NSSM](https://nssm.cc/download) and place `nssm.exe` next to `ModbusOPCUAGateway.exe` **or** add NSSM to `PATH`.
2. Run **as Administrator**: `INSTALL_STARTUP_SERVICE.bat`
3. Service name: `ModbusOPCUAGateway` — auto-start, logs under `logs/service-stdout.log` and `service-stderr.log`.

Uninstall: `scripts/portable/UNINSTALL_STARTUP_SERVICE.bat` or `nssm remove ModbusOPCUAGateway confirm`.

## Fallback: Scheduled Task

If NSSM is not found, the installer registers a **SYSTEM** startup task with the same executable arguments: `--run --portable --config config\gateway.yaml`.

## pywin32 service

A native pywin32 Windows service is **not** shipped in 3.2.x. NSSM or the scheduled task is the supported operator path. A future branch may add `win32serviceutil` if corporate policy forbids NSSM.
