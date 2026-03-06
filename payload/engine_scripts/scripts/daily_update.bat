@echo off
REM ============================================================
REM  DAILY VAULT UPDATE
REM  One-click: rebuild all MOCs, dashboards, and summaries.
REM  Run manually or schedule as a Windows Task.
REM ============================================================

set "SCRIPTS_DIR=O:\_Theophysics_v3\00_SYSTEM\01_ENGINE\scripts"
set "VAULT_ROOT=O:\_Theophysics_v3"

echo.
echo ========================================================
echo   DAILY VAULT UPDATE — %DATE% %TIME%
echo ========================================================
echo.

REM Step 1: Full vault navigation build (MOCs + dashboards)
echo [1/3] Building MOCs and dashboards...
python "%SCRIPTS_DIR%\vault_navigator.py" --full --vault "%VAULT_ROOT%"

REM Step 2: Scripts dashboard
echo.
echo [2/3] Updating scripts dashboard...
python "%SCRIPTS_DIR%\generate_scripts_dashboard.py" --vault "%VAULT_ROOT%"

REM Step 3: Encoding scan (report only, no fix)
echo.
echo [3/3] Quick encoding scan...
python "%SCRIPTS_DIR%\vault_toolkit.py" clean "%VAULT_ROOT%"

echo.
echo ========================================================
echo   DAILY UPDATE COMPLETE — %DATE% %TIME%
echo ========================================================
echo.
pause
