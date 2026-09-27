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

```bat
scripts\build_windows.bat
```

Output: `dist\ModbusOPCUAGateway.exe` with local `config/`, `data/`, `logs/`, `certificates/`.

## Windows Service (Phase 29)

Register with NSSM:

```bat
nssm install ModbusOpcUaGateway "D:\path\to\.venv\Scripts\python.exe" "-m" "app" "--run" "--portable" "--config" "config\gateway.yaml"
```

Or install `pywin32` and extend `app/service/windows_service.py`.
