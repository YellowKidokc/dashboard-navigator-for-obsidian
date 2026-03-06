@echo off
REM Launch VS Code in the Python Backend directory
REM This script opens VS Code in the current project workspace

echo ========================================
echo Launching VS Code for Theophysics Backend
echo ========================================
echo.

REM Change to the Python Backend directory
cd /d "O:\Theophysics_Backend\Python_Backend"

REM Launch VS Code in this directory
code .

echo.
echo VS Code launched!
echo.
pause
