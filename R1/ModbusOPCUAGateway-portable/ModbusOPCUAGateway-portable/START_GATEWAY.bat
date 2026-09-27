@echo off
cd /d "%~dp0"
echo Starting Modbus OPC UA Gateway...
echo Web UI: http://127.0.0.1:8080
echo Close this window or press Ctrl+C to stop.
ModbusOPCUAGateway.exe --run --portable --browser --config config\gateway.yaml
pause
