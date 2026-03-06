@echo off
setlocal enabledelayedexpansion

:: =============================================================================
:: THEOPHYSICS UNIFIED TTS PIPELINE - MASTER LAUNCHER
:: =============================================================================
:: Processes files through:
::   1. Text Normalization (numbers, measures, fractions, dates, etc.)
::   2. Theophysics Translation (Greek symbols, χ-field, equations, axiom refs)
::   3. TTS Engine (Edge = free, OpenAI = premium quality)
::
:: Usage:
::   Double-click to run with defaults (Edge TTS)
::   Or run: LAUNCH_TTS.bat [edge|openai] [voice]
:: =============================================================================

:: --- CONFIGURATION (ABSOLUTE PATHS) ---
set "ENGINE=edge"
set "EDGE_VOICE=en-US-BrianMultilingualNeural"
set "OPENAI_VOICE=onyx"
set "OPENAI_API_KEY="

set "BASE_DIR=O:\Theophysics_Backend\TTS_Engines\TTS_Pipeline"
set "SCRIPT_PATH=%BASE_DIR%\scripts\tts_pipeline.py"
set "INBOX=%BASE_DIR%\batch_launchers\INBOX"
set "OUTBOX=%BASE_DIR%\batch_launchers\OUTBOX"
set "PROCESSED=%BASE_DIR%\batch_launchers\PROCESSED"

:: Python environment
set "VENV_PATH="
if exist "%BASE_DIR%\venv\Scripts\python.exe" (
    set "VENV_PATH=%BASE_DIR%\venv\Scripts\python.exe"
    goto :found_python
)
if exist "O:\Theophysics_Backend\Python_Backend\Backend Python\venv\Scripts\python.exe" (
    set "VENV_PATH=O:\Theophysics_Backend\Python_Backend\Backend Python\venv\Scripts\python.exe"
    goto :found_python
)
set "VENV_PATH=python"
:found_python

:: Parse command line arguments
if not "%~1"=="" set "ENGINE=%~1"
if "%ENGINE%"=="openai" (
    set "VOICE=%OPENAI_VOICE%"
) else (
    set "VOICE=%EDGE_VOICE%"
)
if not "%~2"=="" set "VOICE=%~2"

:: Display banner
echo.
echo ==============================================================
echo    THEOPHYSICS UNIFIED TTS PIPELINE
echo ==============================================================
echo    Engine: %ENGINE%
echo    Voice:  %VOICE%
echo    Inbox:  %INBOX%
echo    Script: %SCRIPT_PATH%
echo    Python: %VENV_PATH%
echo ==============================================================
echo.

:: Create directories if needed
if not exist "%INBOX%" mkdir "%INBOX%"
if not exist "%OUTBOX%" mkdir "%OUTBOX%"
if not exist "%PROCESSED%" mkdir "%PROCESSED%"

:: Check for files
set "FILE_COUNT=0"
for %%F in ("%INBOX%\*.txt" "%INBOX%\*.md") do set /a FILE_COUNT+=1
if %FILE_COUNT%==0 (
    echo [INFO] No files found in INBOX.
    echo [INFO] Place .txt or .md files in: %INBOX%
    echo.
    pause
    exit /b
)

echo [INFO] Found %FILE_COUNT% file(s) to process...
echo.

:: Process each file
for %%F in ("%INBOX%\*.txt" "%INBOX%\*.md") do (
    echo [PROCESSING] %%~nxF
    echo.
    
    :: Build command based on engine
    if "%ENGINE%"=="openai" (
        "%VENV_PATH%" "%SCRIPT_PATH%" "%%F" "%OUTBOX%\%%~nF.mp3" --engine openai --voice %VOICE% --api-key "%OPENAI_API_KEY%" --save-normalized
    ) else (
        "%VENV_PATH%" "%SCRIPT_PATH%" "%%F" "%OUTBOX%\%%~nF.mp3" --engine edge --voice %VOICE% --save-normalized
    )
    
    if !errorlevel! equ 0 (
        echo [SUCCESS] %%~nxF converted
        move "%%F" "%PROCESSED%\" >nul
    ) else (
        echo [ERROR] Failed to convert %%~nxF
    )
    echo.
    echo --------------------------------------------------------------
    echo.
)

echo ==============================================================
echo    ALL DONE!
echo ==============================================================
echo    Outputs saved to: %OUTBOX%
echo    Originals moved to: %PROCESSED%
echo ==============================================================
pause
