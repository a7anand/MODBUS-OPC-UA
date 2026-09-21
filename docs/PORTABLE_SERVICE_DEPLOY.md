# Portable EXE — background service + browser configuration

## Build the package (developer PC)

```bat
scripts\package_release.bat
```

Output:

- `dist\ModbusOPCUAGateway.exe` — single-file executable  
- `dist\ModbusOPCUAGateway-portable.zip` — EXE + `config\`, scripts, docs  

Requires Python venv with `pip install -e ".[dev]"` before building.

## Deploy on another PC (no Python)

1. Unzip `ModbusOPCUAGateway-portable.zip` to e.g. `C:\Gateway\`
2. Optional: replace `config\gateway.yaml` with `examples\gateway.portable-service.yaml` (LAN web + OPC UA).
3. **Background run (recommended):**
   - Double-click `START_BACKGROUND.bat`, or  
   - `ModbusOPCUAGateway.exe --headless`
4. Open browser on that PC (or from LAN): **`http://127.0.0.1:8080/settings`**
   - Set gateway **name**, **Web host/port**, **OPC UA host/port**, Modbus PLC IP, etc.
   - Or use **Full YAML** tab for complete `gateway.yaml` editing.
5. **Auto-start at boot:** Right-click `INSTALL_STARTUP_SERVICE.bat` → Run as administrator (NSSM or scheduled task). See [NSSM_SERVICE.md](NSSM_SERVICE.md).

| Script | Behavior |
|--------|----------|
| `START_BACKGROUND.bat` | No PyQt, no browser popup — Web UI only (console window visible) |
| `START_BACKGROUND_HIDDEN.vbs` | Same as background, **no console window** |
| `START_GATEWAY.bat` | Opens browser to dashboard |
| Double-click EXE | Same as `--headless` (background) |

## Configuration from browser

| Page | Purpose |
|------|---------|
| `/settings` | Name, web bind, OPC UA port, security mode, full YAML editor |
| `/devices` | Modbus TCP/RTU devices (IP, port, …) |
| `/tags` | Tag definitions |
| `/backup` | Backup / restore YAML |

API: `GET/PUT /api/config/settings`, `GET/PUT /api/config/yaml`

**LAN access:** set Web host to `0.0.0.0`, enable **Allow LAN bind**, open Windows Firewall for TCP `8080` (and OPC UA port e.g. `4841`).

**After changing Web host/port:** restart the EXE or Windows service once.

## No desktop GUI

The portable EXE excludes PyQt. All configuration is via the embedded Web UI.
