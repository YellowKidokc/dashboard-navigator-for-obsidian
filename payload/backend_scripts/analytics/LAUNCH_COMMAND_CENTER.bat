@echo off
echo ========================================
echo THEOPHYSICS COMMAND CENTER
echo ========================================
echo.
echo Launching dashboard...
echo.

cd /d "%~dp0"
python THEOPHYSICS_COMMAND_CENTER.py

if errorlevel 1 (
    echo.
    echo ERROR: Failed to launch command center
    pause
)
