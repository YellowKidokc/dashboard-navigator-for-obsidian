@echo off
setlocal EnableExtensions
set "SCRIPT=%~dp0vault_scaffold_builder.py"
if not exist "%SCRIPT%" (
  echo Missing script: "%SCRIPT%"
  exit /b 1
)
python "%SCRIPT%" --interactive
endlocal
