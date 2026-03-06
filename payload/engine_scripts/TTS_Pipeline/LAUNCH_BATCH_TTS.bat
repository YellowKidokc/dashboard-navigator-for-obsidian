@echo off
echo ==============================================================
echo    THEOPHYSICS BATCH TTS PROCESSOR
echo ==============================================================
echo.
echo   1. Processes all .md files in INBOX folder
echo   2. Applies math translation layer
echo   3. Converts to audio (Edge TTS - FREE)
echo   4. Saves to OUTBOX and PROCESSED
echo.
echo Press any key to start...
pause >nul

cd /d "%~dp0"

if not exist "venv\Scripts\python.exe" (
    echo [ERROR] Virtual environment not found!
    echo [INFO]  Run SETUP.bat first.
    pause
    exit /b 1
)

call venv\Scripts\activate
cd scripts
python batch_tts.py --input "..\INBOX" --output "..\OUTBOX" --processed "..\PROCESSED"

echo.
echo ==============================================================
echo    COMPLETE!  Audio files: OUTBOX folder
echo ==============================================================
pause
