@echo off
REM Remove Python and PyInstaller caches. Does not delete config or logs.
cd /d "%~dp0.."
if exist build\*.spec del /q build\*.spec 2>nul
for /d /r %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d"
echo Clean complete.
exit /b 0
