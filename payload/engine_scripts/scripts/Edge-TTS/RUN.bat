@echo off
:: ============================================================
::  Edge TTS  —  Double-click to convert text to speech
:: ============================================================
title Edge TTS — Brian Multilingual
cd /d "%~dp0"

echo.
echo ============================================================
echo   Edge TTS — Text to Speech Processor
echo ============================================================
echo.
echo   Voice  : Brian Multilingual (configurable in config.txt)
echo   Input  : Drop .txt or .md files into input\
echo   Output : MP3 files appear in output\
echo.
echo ============================================================
echo.

:: Check Python is available
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH.
    echo Download it from https://www.python.org/downloads/
    pause
    exit /b 1
)

:: Install edge-tts if missing
python -c "import edge_tts" >nul 2>&1
if %errorlevel% neq 0 (
    echo Installing edge-tts package ...
    pip install edge-tts
    echo.
)

:: Run the processor
python "%~dp0edge_tts_batch.py"

echo.
echo ============================================================
echo   Done!  Check the output\ folder for your MP3 files.
echo ============================================================
pause
