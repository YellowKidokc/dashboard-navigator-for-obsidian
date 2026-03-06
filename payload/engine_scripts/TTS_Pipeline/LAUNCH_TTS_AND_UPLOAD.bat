@echo off
echo ============================================
echo TTS + Google Drive Upload Pipeline
echo ============================================
echo.
echo Options:
echo   1. Full Pipeline (TTS + Upload)
echo   2. TTS Only
echo   3. Upload Only
echo   4. Resume from checkpoint
echo   5. Show Status
echo   6. Clear checkpoint
echo.

REM Go to TTS_Pipeline root
cd /d "%~dp0.."

REM Activate virtual environment
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
)

set /p choice="Enter choice (1-6): "

cd scripts

if "%choice%"=="1" (
    echo.
    echo Starting full pipeline...
    python tts_and_upload.py --input "..\INBOX" --output "..\OUTBOX"
) else if "%choice%"=="2" (
    echo.
    echo Starting TTS only...
    python tts_and_upload.py --input "..\INBOX" --output "..\OUTBOX" --tts-only
) else if "%choice%"=="3" (
    echo.
    echo Starting upload only...
    python tts_and_upload.py --upload-only
) else if "%choice%"=="4" (
    echo.
    echo Resuming from checkpoint...
    python tts_and_upload.py --resume
) else if "%choice%"=="5" (
    echo.
    python tts_and_upload.py --status
) else if "%choice%"=="6" (
    echo.
    python tts_and_upload.py --clear
) else (
    echo Invalid choice
)

echo.
pause
