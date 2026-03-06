@echo off
setlocal EnableExtensions
set "SCRIPT=%~dp0project_yaml_lint.py"
set "VAULT=O:\_Theophysics_v3"
set "REG=O:\_Theophysics_v3\00_SYSTEM\00System\03_Taxonomy_Naming\PROJECT_REGISTRY.csv"

if not exist "%SCRIPT%" (
  echo Missing script: "%SCRIPT%"
  exit /b 1
)

python "%SCRIPT%" --vault-root "%VAULT%" --registry "%REG%"
endlocal
