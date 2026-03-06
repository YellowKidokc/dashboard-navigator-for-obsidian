@echo off
REM Theophysics Manager - Windows Run Script

cd ..

if not exist venv (
    echo ERROR: Virtual environment not found!
    echo Please run install.bat first
    pause
    exit /b 1
)

echo Starting Theophysics Manager...
echo.

call venv\Scripts\activate.bat
python main.py

pause

