@echo off
echo ============================================
echo GET DRIVE LINKS + INSERT INTO PAPERS
echo ============================================
echo.
echo Templates:
echo   - Papers starting with 0: Expanded Content Portal
echo   - Other papers: Simple Quick Access link
echo.
echo Options:
echo   1. Process audio folder only (00-Audio_TTS_LOGOS)
echo   2. Scan ALL Drive folders (finds all 174+ audio files)
echo   3. Refresh ALL links (use after re-doing TTS)
echo   4. Dry run (see what would happen)
echo   5. List audio files in Drive
echo   6. Exit
echo.

REM Go to TTS_Pipeline root
cd /d "%~dp0.."

set /p choice="Enter choice (1-6): "

if "%choice%"=="6" (
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
echo RUNNING...
echo ============================================
echo.

cd scripts

if "%choice%"=="1" (
    python get_drive_links.py
) else if "%choice%"=="2" (
    python get_drive_links.py --scan-all
) else if "%choice%"=="3" (
    python get_drive_links.py --scan-all --refresh
) else if "%choice%"=="4" (
    python get_drive_links.py --scan-all --dry-run
) else if "%choice%"=="5" (
    python get_drive_links.py --scan-all --list
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
