@echo off
:: Run as Administrator: installs gateway to start at Windows boot (background, no browser).
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0windows\Install-GatewayStartup.ps1" -InstallDir "%~dp0"
if %ERRORLEVEL% neq 0 (
  echo.
  echo Right-click this file and choose "Run as administrator"
  pause
  exit /b %ERRORLEVEL%
)
echo.
echo Done. Gateway runs in background; open http://127.0.0.1:8080 in a browser when needed.
pause
