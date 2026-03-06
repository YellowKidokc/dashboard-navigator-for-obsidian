@echo off
REM Launch OpenCode and open it in the Python Backend workspace

echo ========================================
echo Launching OpenCode for Theophysics Backend
echo ========================================
echo.

REM Change to Python Backend directory first
cd /d "O:\Theophysics_Backend\Python_Backend"

REM Launch OpenCode from D drive
echo Starting OpenCode from D:\opencode...
cd /d "D:\opencode"
bun run dev

REM Alternative: If you want to pass the workspace path as an argument
REM bun run dev "O:\Theophysics_Backend\Python_Backend"

pause
