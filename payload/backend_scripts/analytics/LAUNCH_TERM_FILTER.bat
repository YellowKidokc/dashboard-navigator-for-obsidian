@echo off
echo ========================================
echo TERM FILTER GUI
echo ========================================
echo.
echo Opening visual term filter...
echo.

cd /d "%~dp0"
python TERM_FILTER_GUI.py

if errorlevel 1 (
    echo.
    echo ERROR: Failed to launch term filter
    pause
)
