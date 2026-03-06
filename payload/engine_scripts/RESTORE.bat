@echo off
title Vault Rater — RESTORE (Undo Moves)
cd /d "%~dp0"

echo.
echo   ⚠  RESTORE MODE
echo   This will move ALL files back to their original locations
echo   and remove the tier folder structure.
echo.
echo   Press any key to continue, or close this window to cancel.
pause >nul

python "%~dp0vault_rater.py" --restore
pause
