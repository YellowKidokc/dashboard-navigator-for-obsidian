@echo off
echo ========================================
echo  API Query Builder - Standalone Launch
echo ========================================
echo.

cd /d "O:\Theophysics_Backend\Backend Python"

REM Activate venv if exists
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
)

python api_query_launcher.py

pause
