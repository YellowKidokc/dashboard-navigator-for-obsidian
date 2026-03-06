@echo off
REM Theophysics Manager - Windows Installation Script
REM This calls the universal Python installer

echo.
echo ============================================
echo   Theophysics Manager - Installation
echo ============================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found!
    echo Please install Python 3.10+ from https://www.python.org/
    pause
    exit /b 1
)

REM Navigate to project root
cd ..

REM Run universal installer
python scripts\install.py

if errorlevel 1 (
    echo.
    echo Installation encountered errors.
    pause
    exit /b 1
)

echo.
echo Installation complete!
echo.
pause

