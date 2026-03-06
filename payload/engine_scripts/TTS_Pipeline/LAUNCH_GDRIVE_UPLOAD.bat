@echo off
echo ============================================
echo    Google Drive Upload + Link Insertion
echo ============================================
echo.

cd /d "%~dp0"

if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
)

cd scripts
python gdrive_uploader.py %*

echo.
pause
