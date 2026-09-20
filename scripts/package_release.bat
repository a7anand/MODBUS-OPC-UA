@echo off
cd /d "%~dp0.."
call scripts\build_windows.bat
if %ERRORLEVEL% neq 0 exit /b %ERRORLEVEL%
if not exist dist\ModbusOPCUAGateway.exe (
  echo Build failed — no exe in dist\
  exit /b 1
)
set OUT=dist\ModbusOPCUAGateway-portable
if exist "%OUT%" rd /s /q "%OUT%"
mkdir "%OUT%"
copy /y dist\ModbusOPCUAGateway.exe "%OUT%\"
copy /y scripts\portable\START_GATEWAY.bat "%OUT%\"
copy /y scripts\portable\README.txt "%OUT%\"
copy /y scripts\portable\INSTALL_STARTUP_SERVICE.bat "%OUT%\"
copy /y scripts\portable\UNINSTALL_STARTUP_SERVICE.bat "%OUT%\"
xcopy /e /i /y scripts\windows "%OUT%\windows"
xcopy /e /i /y config "%OUT%\config"
xcopy /e /i /y examples "%OUT%\examples"
xcopy /e /i /y docs "%OUT%\docs"
mkdir "%OUT%\data" "%OUT%\backup" "%OUT%\logs" "%OUT%\certificates\own" 2>nul
powershell -NoProfile -Command "Compress-Archive -Path '%OUT%' -DestinationPath 'dist\ModbusOPCUAGateway-portable.zip' -Force"
echo Release: dist\ModbusOPCUAGateway-portable.zip
exit /b 0
