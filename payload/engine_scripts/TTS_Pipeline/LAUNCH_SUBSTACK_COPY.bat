@echo off
REM ================================================
REM SUBSTACK CLIPBOARD TOOL
REM Converts Markdown to HTML and copies to clipboard
REM Ready to paste directly into Substack editor
REM ================================================

echo.
echo ========================================
echo    SUBSTACK CLIPBOARD TOOL
echo ========================================
echo.

REM Check if pandoc is installed
where pandoc >nul 2>nul
if %errorlevel% neq 0 (
    echo ERROR: Pandoc is not installed.
    echo.
    echo Install with: winget install JohnMacFarlane.Pandoc
    echo.
    pause
    exit /b 1
)

REM If no argument, show file picker
if "%~1"=="" (
    echo No file specified. Opening file browser...
    echo.
    powershell -Command "& {Add-Type -AssemblyName System.Windows.Forms; $f = New-Object System.Windows.Forms.OpenFileDialog; $f.Filter = 'Markdown files (*.md)|*.md|Text files (*.txt)|*.txt|All files (*.*)|*.*'; $f.InitialDirectory = '%~dp0OUTBOX'; if($f.ShowDialog() -eq 'OK'){$f.FileName}}" > "%temp%\selected_file.txt"
    set /p INPUTFILE=<"%temp%\selected_file.txt"
    del "%temp%\selected_file.txt"
) else (
    set INPUTFILE=%~1
)

if "%INPUTFILE%"=="" (
    echo No file selected. Exiting.
    pause
    exit /b 1
)

echo Selected file: %INPUTFILE%
echo.
echo Converting to HTML and copying to clipboard...

REM Convert and copy to clipboard using PowerShell
powershell -Command "Get-Content -Raw '%INPUTFILE%' | pandoc -f markdown -t html | Set-Clipboard"

if %errorlevel% equ 0 (
    echo.
    echo ========================================
    echo SUCCESS! HTML copied to clipboard.
    echo.
    echo Next steps:
    echo   1. Go to Substack editor
    echo   2. Press Ctrl+V to paste
    echo   3. Review formatting
    echo   4. Upload audio file if needed
    echo ========================================
    echo.
) else (
    echo.
    echo ERROR: Conversion failed.
    echo Check that the file exists and pandoc is working.
    echo.
)

pause
