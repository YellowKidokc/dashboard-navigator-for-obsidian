@echo off
cd /d "%~dp0"
setlocal
TITLE Theophysics Manager Launcher

echo ========================================================
echo        THEOPHYSICS RESEARCH MANAGER - LAUNCHER
echo ========================================================
echo.

:: 1. Check for Python
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [CRITICAL ERROR] Python is not detected!
    echo FIX: Please install Python 3.10+ from python.org
    echo      Make sure to check "Add Python to PATH" during installation.
    goto :ErrorExit
)
echo [CHECK] Python is installed.

:: 2. Check for Virtual Environment
if exist "venv\Scripts\activate.bat" (
    echo [CHECK] Virtual environment found. Activating...
    call venv\Scripts\activate.bat
) else (
    echo [WARNING] No virtual environment 'venv' found. Using global Python.
    echo           It is recommended to run: python -m venv venv
)

:: 3. Check for main.py
if not exist "main.py" (
    echo [CRITICAL ERROR] main.py not found in current directory!
    echo FIX: Ensure you are running this script from the 'theophysics_manager' folder.
    goto :ErrorExit
)
echo [CHECK] main.py found.

:: 4. Dependency Check (PySide6)
echo [INFO] Verifying dependencies...
python -c "import PySide6" >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Required libraries (PySide6) are missing.
    echo [ACTION] Attempting to install from requirements.txt...
    if exist "requirements.txt" (
        pip install -r requirements.txt
        if %ERRORLEVEL% NEQ 0 (
             echo [CRITICAL ERROR] Failed to install dependencies.
             echo FIX: Check your internet connection or pip configuration.
             goto :ErrorExit
        )
        echo [SUCCESS] Dependencies installed.
    ) else (
        echo [CRITICAL ERROR] PySide6 is missing and requirements.txt is missing!
        echo FIX: Restore requirements.txt or install PySide6 manually.
        goto :ErrorExit
    )
) else (
    echo [CHECK] Dependencies verified.
)

:: 5. Launch
echo.
echo ========================================================
echo System Ready. Auto-launching...
echo ========================================================
timeout /t 2 /nobreak >nul

python app_v2.py > launch_log.txt 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ========================================================
    echo [APP CRASH] The application exited with errors.
    echo errors are logged to 'launch_log.txt'. Here is the content:
    echo --------------------------------------------------------
    type launch_log.txt
    echo --------------------------------------------------------
    echo FIX: Read the traceback above. Common issues:
    echo      - Database locked (close DB tools)
    echo      - Missing assets (check paths)
    echo      - API Key issues (check env vars)
    echo      - VC++ Redistributable missing (install it)
    echo ========================================================
) else (
    echo.
    echo [INFO] Application closed successfully.
    echo [LOG] Run details saved to launch_log.txt
)

:ErrorExit
echo.
echo ========================================================
echo Script finished. Press ENTER to close this window.
echo ========================================================
pause >nul
