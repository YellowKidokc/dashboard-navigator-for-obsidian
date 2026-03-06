@echo off
REM ============================================================
REM PRODUCTION PAPER FORMATTER
REM ============================================================
REM Production-grade tool for 31,000+ documents
REM
REM Features:
REM - Checkpoint/resume (survives reboots)
REM - Error resilience (one bad file doesn't stop batch)
REM - Progress tracking
REM - Comprehensive logging
REM
REM Author: David Lowe / Theophysics Project
REM ============================================================

echo.
echo ============================================================
echo PRODUCTION PAPER FORMATTER
echo For processing 31,000+ documents
echo ============================================================
echo.

REM Check venv
if not exist "venv\" (
    echo [ERROR] Virtual environment not found!
    echo Please run SETUP.bat first.
    pause
    exit /b 1
)

REM Launch
echo Starting production formatter...
echo.

call venv\Scripts\activate.bat
python format_papers_production.py

if errorlevel 1 (
    echo.
    echo [ERROR] Formatter encountered an error.
    pause
    exit /b 1
)

echo.
echo Formatter closed.
pause
