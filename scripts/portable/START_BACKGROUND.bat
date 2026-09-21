@echo off
:: Headless gateway (no PyQt, no browser popup). Configure via Web UI.
cd /d "%~dp0"
echo Modbus OPC UA Gateway — background mode
echo Web UI: http://127.0.0.1:8080/settings  (change port in config if needed)
echo Install at startup: run INSTALL_STARTUP_SERVICE.bat as Administrator
ModbusOPCUAGateway.exe --headless --config config\gateway.yaml
