@echo off
setlocal

set "SCRIPT_DIR=%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%SCRIPT_DIR%LAUNCH_THEOPHYSICS_BACKEND_V2.ps1"

if errorlevel 1 (
  echo.
  echo Launch failed.
  pause
  exit /b 1
)

exit /b 0
