@echo off
REM Launch OpenCode for the Axioms workspace

echo ========================================
echo Launching OpenCode for Axioms Folder
echo ========================================
echo.

REM Change to Axioms directory
cd /d "O:\Theophysics_Master\TMSUB\GO FOLDER\_AXIOMS_001-188"

REM Launch OpenCode from D drive
echo Starting OpenCode from D:\opencode...
cd /d "D:\opencode"
bun run dev

pause
