Modbus OPC UA Gateway (portable)

1. Run ModbusOPCUAGateway.exe (double-click) OR START_GATEWAY.bat
2. Browser opens to http://127.0.0.1:8080 — full web UI:
   Dashboard, Devices, Tags, Import, Polling, Trends, History, Traffic, Diagnostics
3. Edit config\gateway.yaml or use the browser; backups in backup\
4. OPC UA: see opcua.server.endpoint in gateway.yaml

Folders beside the EXE: config, data, logs, backup

Double-click EXE = gateway + browser (no arguments needed).

BACKGROUND AT STARTUP (no browser):
  Right-click INSTALL_STARTUP_SERVICE.bat -> Run as administrator
  Uses Windows Scheduled Task (or NSSM if nssm.exe is in this folder).
  Web UI stays at http://127.0.0.1:8080 when you need it.

Remove: UNINSTALL_STARTUP_SERVICE.bat (as admin).
