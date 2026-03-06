@echo off
title Vault Rater — Statistics
cd /d "%~dp0"
python "%~dp0vault_rater.py" --stats
pause
