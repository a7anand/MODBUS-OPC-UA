# Windows startup / background service

Run the gateway **without** opening a browser, starting automatically when Windows boots.

## Portable EXE (recommended)

1. Extract `ModbusOPCUAGateway-portable.zip` to a fixed path, e.g. `C:\Gateway\`.
2. Edit `config\gateway.yaml` (devices, OPC UA endpoint, web port).
3. **Right-click** `INSTALL_STARTUP_SERVICE.bat` → **Run as administrator**.

The installer:

- Runs `ModbusOPCUAGateway.exe --run --portable --config config\gateway.yaml` (no `--browser`).
- Registers **Scheduled Task** `ModbusOPCUAGateway` at **system startup** (runs as `SYSTEM`).
- If `nssm.exe` is in the same folder (or on `PATH`), installs a **Windows Service** instead (auto-restart, service control panel).

Open the UI anytime: **http://127.0.0.1:8080** (or your `web.host` / `web.port`).

### Remove startup

Right-click `UNINSTALL_STARTUP_SERVICE.bat` → Run as administrator.

### Optional: NSSM (true Windows service)

1. Download [NSSM](https://nssm.cc/download) and copy `nssm.exe` into the gateway folder next to the EXE.
2. Run `INSTALL_STARTUP_SERVICE.bat` again as admin.

Manual NSSM:

```bat
nssm install ModbusOPCUAGateway "C:\Gateway\ModbusOPCUAGateway.exe" --run --portable --config config\gateway.yaml
nssm set ModbusOPCUAGateway AppDirectory C:\Gateway
nssm set ModbusOPCUAGateway Start SERVICE_AUTO_START
nssm start ModbusOPCUAGateway
```

## Python / development install

```bat
nssm install ModbusOpcUaGateway "D:\path\.venv\Scripts\python.exe" "-m" "app" "--run" "--portable" "--config" "config\gateway.yaml"
nssm set ModbusOpcUaGateway AppDirectory D:\path\OPC-MODBUS
nssm set ModbusOpcUaGateway Start SERVICE_AUTO_START
```

Or:

```bat
python -m app --run --portable --service --config config\gateway.yaml
```

(with NSSM pointing at the same command line).

## Logs

- Portable EXE: `logs\` next to the executable.
- NSSM service: `logs\service-stdout.log` and `service-stderr.log` (configured by the install script).

## Firewall

Allow inbound **TCP** for your web port (default **8080**) and OPC UA (e.g. **4841**) if remote clients connect.
