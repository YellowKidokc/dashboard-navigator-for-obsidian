@echo off
setlocal
title Theophysics Research Manager V2

echo.
echo ========================================
echo   Theophysics Research Manager V2
echo   Sidebar Navigation Edition
echo ========================================
echo.

cd /d "%~dp0"

if not exist "app_v2.py" (
    echo ERROR: app_v2.py not found in this folder.
    goto :error_exit
)

set "PYTHON_CMD=python"

if exist "venv\Scripts\activate.bat" (
    echo Activating virtual environment...
    call venv\Scripts\activate.bat
) else (
    echo No virtual environment found, using system Python
)

if exist "venv\Scripts\python.exe" (
    set "PYTHON_CMD=venv\Scripts\python.exe"
)

echo Checking core dependencies...
%PYTHON_CMD% -c "import PySide6, psycopg2, yaml, requests, numpy, pandas, openpyxl" >nul 2>&1
if errorlevel 1 (
    echo Missing dependencies detected. Attempting auto-repair...
    %PYTHON_CMD% -m pip install --disable-pip-version-check PySide6 psycopg2-binary pyyaml requests numpy pandas openpyxl beautifulsoup4 markdownify lxml tqdm > launch_repair_log.txt 2>&1
    if errorlevel 1 (
        echo.
        echo ========================================
        echo ERROR: Dependency auto-repair failed
        echo ========================================
        echo See launch_repair_log.txt for details.
        type launch_repair_log.txt
        goto :error_exit
    )
    echo Dependency auto-repair complete.
)

echo Starting application...
echo.

%PYTHON_CMD% app_v2.py > launch_log.txt 2>&1
if errorlevel 1 (
    echo.
    echo ========================================
    echo ERROR: Application exited with error
    echo ========================================
    echo Traceback from launch_log.txt:
    echo ----------------------------------------
    type launch_log.txt
    echo ----------------------------------------
    goto :error_exit
)

echo Application closed successfully.
goto :eof

:error_exit
echo.
echo Press any key to continue . . .
pause >nul
