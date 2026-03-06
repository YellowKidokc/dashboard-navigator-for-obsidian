@echo off
:: ============================================================
::  THEOPHYSICS - RUN ALL ANALYTICS (Unified Analyzer + Full Suite)
::  Runs: Vault Rater, Python Backend Analytics, Adam & Eve, Full Vault
:: ============================================================
title Theophysics - Run All Analytics
cd /d "%~dp0"

set VAULT=O:\_Theophysics_v3
set ADAM_EVE=O:\_Theophysics_v3\02_THEOPHYSICS\Theological\Adam and Eve
set ANALYTICS=%~dp0analytics
set THEOPHYSICS_VAULT=O:\_Theophysics_v3

echo.
echo ============================================================
echo   THEOPHYSICS - RUN ALL ANALYTICS
echo ============================================================
echo   Vault: %VAULT%
echo   Adam and Eve: %ADAM_EVE%
echo ============================================================
echo.

:: 1. Vault Rater - Full pass on Adam and Eve
echo [1/4] Running Vault Rater (TSR-100) on Adam and Eve...
cd "O:\_Theophysics_v3\00_SYSTEM\01_ENGINE"
python vault_rater.py --vault "%ADAM_EVE%" --pass both
if %ERRORLEVEL% NEQ 0 (
    echo WARNING: Vault rater had issues. Continuing...
)
echo.

:: 2. Custom Dashboard on Adam and Eve (Fruits of Spirit, 50 metrics)
echo [2/4] Running Custom Dashboard on Adam and Eve...
cd "%~dp0analytics"
python custom_dashboard_runner.py "%ADAM_EVE%" "%VAULT%\_vault_rater\Adam_and_Eve_Dashboard"
if %ERRORLEVEL% NEQ 0 (
    echo WARNING: Custom dashboard had issues. Continuing...
)
echo.

:: 3. Full Analytics Suite (from analytics folder)
echo [3/4] Running Full Analytics Suite...
cd "%~dp0analytics"
call RUN_FULL_ANALYTICS.bat
if %ERRORLEVEL% NEQ 0 (
    echo WARNING: Full analytics had issues. Continuing...
)
echo.

:: 4. Vault Rater Stats on full vault
echo [4/4] Running Vault Rater Stats on full vault...
cd "O:\_Theophysics_v3\00_SYSTEM\01_ENGINE"
python vault_rater.py --vault "%VAULT%" --stats
echo.

echo ============================================================
echo   COMPLETE! All analytics runs finished.
echo ============================================================
echo   Results:
echo   - Adam and Eve ratings: %ADAM_EVE%\_vault_rater\
echo   - Adam and Eve dashboard: %VAULT%\_vault_rater\Adam_and_Eve_Dashboard\
echo   - Full vault stats: See above
echo   - Analytics output: Check Global_Analytics folder
echo ============================================================
pause
