@echo off
echo ========================================
echo   VAULT ANALYTICS REPORT GENERATOR
echo ========================================
echo.
echo Dark theme, dense metrics, layered analysis.
echo.

cd /d "O:\Theophysics_Backend\Backend Python"

echo Running analysis...
python scripts\vault_analytics.py

echo.
echo Opening report...
start "" "O:\Theophysics_Master\TM\00_VAULT_OS\Reports\vault_analytics.html"

echo.
echo Done!
pause
