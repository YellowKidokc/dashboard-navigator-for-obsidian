@echo off
echo ==============================================================
echo    MATH TRANSLATION MANAGER
echo ==============================================================
echo.

cd /d "%~dp0"

if not exist "venv\Scripts\python.exe" (
    echo [ERROR] Virtual environment not found! Run SETUP.bat first.
    pause
    exit /b 1
)

call venv\Scripts\activate.bat
cd scripts
python math_translation_manager.py

echo.
echo Application closed.
pause
