@echo off
setlocal

set "SCRIPT=O:\_Theophysics_v3\00_SYSTEM\01_ENGINE\scripts\archive_master_eq_snapshot.ps1"

if "%~1"=="" (
  echo Usage: ARCHIVE_MASTER_EQ_SNAPSHOT.bat ^<SnapshotFolderName^>
  echo Example: ARCHIVE_MASTER_EQ_SNAPSHOT.bat Axioms_Production_Vault_20260217_123014
  exit /b 1
)

powershell -NoProfile -ExecutionPolicy Bypass -File "%SCRIPT%" -SourceFolderName "%~1"
exit /b %ERRORLEVEL%
