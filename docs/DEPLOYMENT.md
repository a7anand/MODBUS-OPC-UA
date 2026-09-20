# Deployment

## Run headless

```bat
python -m app --run --config config\gateway.yaml
```

Web UI: `http://127.0.0.1:8080`  
OPC UA: configured `opcua.server.endpoint` (default `opc.tcp://0.0.0.0:4840`)

## PyQt GUI

```bat
pip install PyQt5
python -m app --gui --config config\gateway.yaml
```

## Portable EXE (Phase 28)

Build:

```bat
scripts\package_release.bat
```

Outputs:

- `dist\ModbusOPCUAGateway.exe` — single-file gateway (embedded web UI)
- `dist\ModbusOPCUAGateway-portable.zip` — EXE + `config/`, `examples/`, `docs/`, `START_GATEWAY.bat`

**Run (end user):** extract the zip, double-click `ModbusOPCUAGateway.exe` (opens browser at `http://127.0.0.1:8080`) or use `START_GATEWAY.bat`. Writable folders (`config`, `data`, `logs`, `backup`) are created beside the EXE.

## Windows Service / startup at boot

See **`docs/WINDOWS_STARTUP_SERVICE.md`**.

Portable package: run **`INSTALL_STARTUP_SERVICE.bat`** as Administrator (in the extracted folder).

Dev / NSSM:

```bat
nssm install ModbusOpcUaGateway "D:\path\to\.venv\Scripts\python.exe" "-m" "app" "--run" "--portable" "--config" "config\gateway.yaml"
```
