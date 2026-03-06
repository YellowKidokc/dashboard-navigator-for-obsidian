@echo off
echo ============================================
echo SMART UPLOAD TO GOOGLE DRIVE
echo ============================================
echo.
echo This will:
echo   1. Find all audio files in OUTBOX
echo   2. Match each to its source paper
echo   3. Upload to correct Drive folder
echo   4. Insert shareable link into paper
echo   5. Delete local audio file
echo.
echo Options:
echo   1. Upload and process (normal)
echo   2. Dry run (see what would happen)
echo   3. Upload but keep local files
echo   4. Exit
echo.

cd /d "%~dp0"

set /p choice="Enter choice (1-4): "

if "%choice%"=="4" (
    echo.
    echo Exiting...
    goto :end
)

echo.
echo ============================================
echo ACTIVATING ENVIRONMENT...
echo ============================================

if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
    echo [OK] Virtual environment activated
) else (
    echo [WARNING] No venv found, using system Python
)

echo.
echo ============================================
echo RUNNING UPLOAD SCRIPT...
echo ============================================
echo.

if "%choice%"=="1" (
    python smart_upload_to_drive.py
) else if "%choice%"=="2" (
    python smart_upload_to_drive.py --dry-run
) else if "%choice%"=="3" (
    python smart_upload_to_drive.py --keep-local
) else (
    echo [ERROR] Invalid choice: %choice%
)

echo.
echo ============================================
echo PROCESS COMPLETE
echo ============================================
echo.
echo Review the output above for any errors.
echo.

:end
echo Press any key to close this window...
pause >nul
