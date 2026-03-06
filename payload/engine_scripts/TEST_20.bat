@echo off
title Vault Rater — Test Run (20 files)
cd /d "%~dp0"

echo.
echo   TEST RUN — Rating 20 files only (both passes)
echo   This costs pennies and lets you verify before full run.
echo.

python "%~dp0vault_rater.py" --pass both --limit 20 --skip-move
pause
