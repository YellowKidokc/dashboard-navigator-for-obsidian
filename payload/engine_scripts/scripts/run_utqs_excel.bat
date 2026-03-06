@echo off
setlocal EnableExtensions
set "SCRIPT=%~dp0utqs_excel_checker.py"
set "WB=O:\_Theophysics_v3\00_SYSTEM\00System\08_Quality_Scoring_Model\UTQS_Rating_Template.xlsx"

if not exist "%SCRIPT%" (
  echo Missing script: "%SCRIPT%"
  exit /b 1
)

if not exist "%WB%" (
  echo Initializing workbook...
  python "%SCRIPT%" --workbook "%WB%" --init-workbook
)

python "%SCRIPT%" --workbook "%WB%" --score-workbook
endlocal
