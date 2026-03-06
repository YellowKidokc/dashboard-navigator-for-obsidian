@echo off
REM Install voice-to-text tools

echo ========================================
echo Installing Voice-to-Text Tools
echo ========================================
echo.

cd /d "O:\Theophysics_Backend\Python_Backend"

echo Installing required packages...
echo This will install:
echo   - openai-whisper (transcription)
echo   - sounddevice (microphone recording)
echo   - soundfile (audio file handling)
echo   - pyperclip (clipboard access)
echo.

pip install openai-whisper sounddevice soundfile pyperclip

if %errorlevel% neq 0 (
    echo.
    echo ERROR: Installation failed!
    pause
    exit /b 1
)

echo.
echo ========================================
echo Installation Complete!
echo ========================================
echo.
echo To use:
echo   python voice_to_text.py
echo.
echo Or use: voice_record.bat
echo.
pause
