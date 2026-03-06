@echo off
REM ============================================
REM    SYNOLOGY NAS BACKUP SCRIPT
REM    Syncs Theophysics vault to NAS
REM ============================================

REM === CONFIGURATION ===
set NAS_IP=192.168.1.177
set NAS_SHARE=Theophysics
set NAS_USER=Yellowkid
set NAS_PASS=Moss9pep28$

set SOURCE_VAULT=C:\Users\Yellowkid\Documents\Theophysics Master SYNC

echo.
echo ============================================
echo    BACKING UP TO SYNOLOGY NAS
echo    NAS: %NAS_IP%
echo    Share: %NAS_SHARE%
echo ============================================
echo.

REM Map network drive (if not already mapped)
net use Z: \\%NAS_IP%\%NAS_SHARE% /user:%NAS_USER% %NAS_PASS% /persistent:no 2>nul

if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Could not connect to NAS at %NAS_IP%
    echo Check: IP address, share name, username, password
    pause
    exit /b 1
)

echo [OK] Connected to NAS

REM Backup Vault
echo.
echo Syncing Theophysics Vault...
robocopy "%SOURCE_VAULT%" "Z:\Theophysics_Vault" /MIR /XD .obsidian .git __pycache__ node_modules venv /XF *.db *.log /R:3 /W:5 /NP /NDL

REM Disconnect network drive
net use Z: /delete /y 2>nul

echo.
echo ============================================
echo    BACKUP COMPLETE!
echo    %date% %time%
echo ============================================
pause
