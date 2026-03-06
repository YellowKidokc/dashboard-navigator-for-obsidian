@echo off
echo ============================================================
echo    PAPER FORMATTER - 4-Layer Equation Translation
echo ============================================================
echo.

cd /d "%~dp0"

if not exist "venv\Scripts\python.exe" (
    echo [ERROR] Virtual environment not found! Run SETUP.bat first.
    pause
    exit /b 1
)

call venv\Scripts\activate.bat
cd scripts
python format_papers_gui.py

echo.
echo Paper Formatter closed.
pause
