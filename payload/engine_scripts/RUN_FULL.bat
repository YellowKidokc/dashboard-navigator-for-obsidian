@echo off
:: ============================================================
::  Theophysics Vault Rater — Full Run
::  Double-click to rate your entire vault
:: ============================================================
title Theophysics Vault Rater
cd /d "%~dp0"

if "%THEOPHYSICS_VAULT_PATH%"=="" set "THEOPHYSICS_VAULT_PATH=O:\_Theophysics_v3"

echo.
echo ============================================================
echo   THEOPHYSICS VAULT RATER
echo   TSR-100 Derived Rating System
echo ============================================================
echo.
echo   Vault:  %THEOPHYSICS_VAULT_PATH%
echo   Pass 1: gpt-4o-mini triage (A/B/C/D)
echo   Pass 2: gpt-4o deep rating (A-tier only)
echo.
echo   Output: YAML frontmatter + tier folders + CSV
echo ============================================================
echo.

:: Check Python
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python not found. Install from https://www.python.org
    pause
    exit /b 1
)

:: Install openai if needed
python -c "import openai" >nul 2>&1
if %errorlevel% neq 0 (
    echo Installing OpenAI package...
    pip install openai
    echo.
)

:: Check config
if not exist "%~dp0config.txt" (
    echo ERROR: config.txt not found!
    echo Copy config.example.txt to config.txt and add your API key.
    pause
    exit /b 1
)

:: Run both passes
python "%~dp0vault_rater.py" --pass both

echo.
echo ============================================================
echo   Done! Check %THEOPHYSICS_VAULT_PATH%\_vault_rater\ for results.
echo ============================================================
pause
