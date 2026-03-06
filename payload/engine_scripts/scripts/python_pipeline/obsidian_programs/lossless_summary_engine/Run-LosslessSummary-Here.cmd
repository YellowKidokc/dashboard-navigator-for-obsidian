@echo off
setlocal
set "SCRIPT_DIR=%~dp0"
set "PS_SCRIPT=%SCRIPT_DIR%build_lossless_summary.ps1"

if not exist "%PS_SCRIPT%" (
  echo Missing script: %PS_SCRIPT%
  pause
  exit /b 1
)

echo Running lossless summary for:
echo   %SCRIPT_DIR%
echo.

powershell -NoProfile -ExecutionPolicy Bypass -File "%PS_SCRIPT%" -TargetPath "%SCRIPT_DIR%"

echo.
echo Done.
pause
endlocal
