@echo off
echo ========================================
echo  THEOPHYSICS STAGE GENERATOR
echo ========================================
echo.

cd /d "%~dp0"

REM Activate virtual environment if exists
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
)

echo Running Stage Generator...
python scripts\generate_stages.py %*

pause
