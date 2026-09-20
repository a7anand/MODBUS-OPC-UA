@echo off
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0windows\Uninstall-GatewayStartup.ps1" -InstallDir "%~dp0"
if %ERRORLEVEL% neq 0 (
  echo Right-click and Run as administrator
)
pause
