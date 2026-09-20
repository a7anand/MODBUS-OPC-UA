@echo off
cd /d "%~dp0.."
if not exist .venv\Scripts\python.exe (
  echo Create venv and pip install -r requirements\dev.txt first.
  exit /b 1
)
.venv\Scripts\pip install pyinstaller openpyxl python-multipart websockets -q
.venv\Scripts\pyinstaller build\gateway.spec --distpath dist --workpath build\pyi --noconfirm
echo Build output: dist\ModbusOPCUAGateway.exe
exit /b 0
