@echo off
echo ========================================
echo    BATCH SUBSTACK PUBLISHER
echo ========================================
echo.

cd /d "%~dp0"
powershell -ExecutionPolicy Bypass -File "scripts\substack_batch_publisher.ps1" -CopyFirst

echo.
pause
