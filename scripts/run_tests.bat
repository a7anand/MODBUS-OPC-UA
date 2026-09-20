@echo off
cd /d "%~dp0.."
python -m pytest tests -q
exit /b %ERRORLEVEL%
