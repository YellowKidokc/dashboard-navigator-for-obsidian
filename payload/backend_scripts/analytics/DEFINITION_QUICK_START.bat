@echo off
echo ============================================
echo   THEOPHYSICS DEFINITION SYSTEM
echo   Quick Start Menu
echo ============================================
echo.

cd /d "%~dp0"

:menu
echo.
echo What would you like to do?
echo.
echo   1. Test the system (run example)
echo   2. Create definitions interactively
echo   3. Scan vault and auto-generate
echo   4. View documentation
echo   5. Exit
echo.

set /p choice="Choice (1-5): "

if "%choice%"=="1" goto test
if "%choice%"=="2" goto create
if "%choice%"=="3" goto scan
if "%choice%"=="4" goto docs
if "%choice%"=="5" goto end

echo Invalid choice. Please try again.
goto menu

:test
echo.
echo Running test with sample terms...
echo.
python TEST_DEFINITIONS.py
pause
goto menu

:create
echo.
echo Launching interactive definition creator...
echo.
python CREATE_DEFINITIONS.py
pause
goto menu

:scan
echo.
echo Launching vault scanner...
echo.
python SCAN_AND_DEFINE.py
pause
goto menu

:docs
echo.
echo Opening documentation...
start DEFINITION_SYSTEM_GUIDE.md
goto menu

:end
echo.
echo Goodbye!
echo.
