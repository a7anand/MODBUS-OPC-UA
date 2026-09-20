@echo off
echo Legacy build (Phase 30): requires Python 3.8 venv and requirements\legacy.txt
echo This branch is NOT validated. See docs\WINDOWS_COMPATIBILITY.md
echo.
echo Steps:
echo   py -3.8 -m venv .venv-legacy
echo   .venv-legacy\Scripts\pip install -r requirements\legacy.txt
echo   REM Port incompatible APIs from app/ before building — manual merge track.
exit /b 1
