@echo off
title Vault Rater — Dry Run (Cost Estimate)
cd /d "%~dp0"
python "%~dp0vault_rater.py" --dry-run
pause
