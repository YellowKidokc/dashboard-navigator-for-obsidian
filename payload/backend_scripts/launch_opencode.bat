@echo off
REM Launch OpenCode from D drive
REM OpenCode is a command-line AI development tool

echo ========================================
echo Launching OpenCode
echo ========================================
echo.

REM Change to OpenCode directory
cd /d "D:\opencode"

REM Launch OpenCode using bun (the package manager it uses)
echo Starting OpenCode...
bun run dev

REM If bun is not in PATH, you can use the full path:
REM "D:\path\to\bun.exe" run dev

pause
