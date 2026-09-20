@echo off
cd /d "%~dp0.."
call scripts\build_windows.bat
exit /b %ERRORLEVEL%
