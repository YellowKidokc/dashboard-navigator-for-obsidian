@echo off
echo ============================================
echo TTS Bundle for Google Drive
echo ============================================
echo.
echo Options:
echo   1. Bundle files + Get Drive links
echo   2. Bundle only (wait for GoodSync)
echo   3. Get links only (files already synced)
echo.

cd /d "%~dp0"

if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
)

set /p choice="Enter choice (1-3): "

if "%choice%"=="1" (
    python bundle_for_drive.py
) else if "%choice%"=="2" (
    python bundle_for_drive.py --bundle-only
) else if "%choice%"=="3" (
    python bundle_for_drive.py --get-links
) else (
    echo Invalid choice
)

echo.
pause
