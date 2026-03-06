@echo off
REM Quick dependency installer/updater
REM Run this if you get import errors or after pulling updates

echo ==============================================================
echo    INSTALLING/UPDATING TTS PIPELINE DEPENDENCIES
echo ==============================================================
echo.

cd /d "%~dp0"

REM Check if venv exists
if not exist "venv\Scripts\python.exe" (
    echo [ERROR] Virtual environment not found!
    echo [INFO] Run SETUP.bat first to create the environment.
    echo.
    pause
    exit /b 1
)

REM Activate venv
echo [1/3] Activating virtual environment...
call venv\Scripts\activate.bat

REM Update pip
echo [2/3] Updating pip...
python -m pip install --upgrade pip

REM Install/update all requirements
echo [3/3] Installing dependencies from requirements.txt...
pip install -r requirements.txt --upgrade

echo.
echo ==============================================================
echo    DEPENDENCY INSTALLATION COMPLETE
echo ==============================================================
echo.
echo Testing key imports...
python -c "import edge_tts; print('  [OK] edge-tts')" || echo   [FAIL] edge-tts
python -c "import pandas; print('  [OK] pandas')" || echo   [FAIL] pandas
python -c "import openpyxl; print('  [OK] openpyxl')" || echo   [FAIL] openpyxl
python -c "from theophysics_normalizer import TheophysicsNormalizer; print('  [OK] theophysics_normalizer')" || echo   [FAIL] theophysics_normalizer

echo.
echo All dependencies installed!
echo You can now use any of the LAUNCH_*.bat files.
echo.
pause
