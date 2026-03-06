@echo off
title Theophysics Research Manager V2
echo.
echo ========================================
echo   Theophysics Research Manager V2
echo   Sidebar Navigation Edition
echo ========================================
echo.

cd /d "%~dp0"

REM Check if venv exists
if exist "venv\Scripts\activate.bat" (
    echo Activating virtual environment...
    call venv\Scripts\activate.bat
) else (
    echo No virtual environment found, using system Python
)

echo Starting application...
echo.

python app_v2.py

if errorlevel 1 (
    echo.
    echo ========================================
    echo ERROR: Application exited with error
    echo ========================================
    pause
)
