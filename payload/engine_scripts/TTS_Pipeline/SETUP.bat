@echo off
echo ==============================================================
echo    THEOPHYSICS TTS PIPELINE - SETUP
echo ==============================================================
echo.

cd /d "%~dp0"
set "ROOT_DIR=%CD%"

python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Please install Python 3.8+
    pause
    exit /b 1
)

if not exist "venv" (
    echo [1/4] Creating virtual environment...
    python -m venv venv
) else (
    echo [1/4] Virtual environment already exists.
)

echo [2/4] Activating virtual environment...
call venv\Scripts\activate.bat

echo [3/4] Installing dependencies...
pip install --upgrade pip
pip install -r config\requirements.txt

echo [4/4] Testing installation...
cd scripts
python -c "import edge_tts; print('  [OK] edge-tts')"
python -c "import pandas; print('  [OK] pandas')"
python -c "import openpyxl; print('  [OK] openpyxl')"
python -c "from theophysics_normalizer import TheophysicsNormalizer; n = TheophysicsNormalizer(); print('  [OK] Normalizer loaded')"
cd ..

echo.
echo ==============================================================
echo    SETUP COMPLETE!
echo ==============================================================
echo.
echo   1. Drop .md files into the INBOX folder
echo   2. Run LAUNCH_BATCH_TTS.bat
echo   3. Audio appears in OUTBOX
echo.
pause
