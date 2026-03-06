@echo off
REM LAUNCH.bat - Quick launcher for LAUNCHER.ps1
REM Double-click this file to start the unified menu system

powershell.exe -ExecutionPolicy Bypass -File "%~dp0LAUNCHER.ps1"
pause
