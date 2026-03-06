@echo off
setlocal

echo ========================================
echo   VAULT ANALYTICS REPORT GENERATOR
echo ========================================
echo.
echo Dense analytics pipeline with centralized output hub.
echo.

if not defined ANALYTICS_ROOT set ANALYTICS_ROOT=O:\999_IGNORE\Obsidian Data Analytics
if not defined ANALYTICS_ENGINE set ANALYTICS_ENGINE=%ANALYTICS_ROOT%\02_Python_Engine
if not defined ANALYTICS_TOOLKIT_RUNNER set ANALYTICS_TOOLKIT_RUNNER=%ANALYTICS_ROOT%\Scripts\Tools\RUN.bat
if not defined ANALYTICS_AUDIT_SCRIPT set ANALYTICS_AUDIT_SCRIPT=%ANALYTICS_ROOT%\Scripts\unification_audit_extract.py
if not defined ANALYTICS_VAULT set ANALYTICS_VAULT=O:\_Theophysics_v3\04_THEOPYHISCS\THREE TRUTHS
if not defined ANALYTICS_OUTPUT_PATH set ANALYTICS_OUTPUT_PATH=%ANALYTICS_ROOT%\03_Dashboards
if not defined ANALYTICS_AUDIT_OUTPUT set ANALYTICS_AUDIT_OUTPUT=%ANALYTICS_OUTPUT_PATH%\Unification_Audit
if not defined ANALYTICS_RUN_UNIFICATION_AUDIT set ANALYTICS_RUN_UNIFICATION_AUDIT=1
if not defined FORMULA_SCRIPTS_PATH set FORMULA_SCRIPTS_PATH=%ANALYTICS_VAULT%\00_OS\Scripts
if not defined ANALYTICS_PYTHON if exist "O:\999_IGNORE\Obsidian Programs\Python_Backend\venv\Scripts\python.exe" set ANALYTICS_PYTHON=O:\999_IGNORE\Obsidian Programs\Python_Backend\venv\Scripts\python.exe

echo Analytics Root  : %ANALYTICS_ROOT%
echo Engine Path     : %ANALYTICS_ENGINE%
echo Toolkit Runner  : %ANALYTICS_TOOLKIT_RUNNER%
echo Audit Script    : %ANALYTICS_AUDIT_SCRIPT%
echo Target Vault    : %ANALYTICS_VAULT%
echo Output Hub      : %ANALYTICS_OUTPUT_PATH%
echo Audit Output    : %ANALYTICS_AUDIT_OUTPUT%
if defined ANALYTICS_PYTHON echo Python Runtime  : %ANALYTICS_PYTHON%
echo.

if not exist "%ANALYTICS_ENGINE%\RUN_COMPLETE_ANALYTICS.bat" (
  echo ERROR: Missing runner:
  echo   %ANALYTICS_ENGINE%\RUN_COMPLETE_ANALYTICS.bat
  pause
  exit /b 1
)

cd /d "%ANALYTICS_ENGINE%"
call RUN_COMPLETE_ANALYTICS.bat
if errorlevel 1 (
  echo.
  echo Analytics pipeline failed.
  pause
  exit /b 1
)

echo.
echo ============================================================
echo   Running Toolkit Classifier
echo ============================================================
if exist "%ANALYTICS_TOOLKIT_RUNNER%" (
  set TOOLKIT_NO_PAUSE=1
  call "%ANALYTICS_TOOLKIT_RUNNER%"
  if errorlevel 1 (
    echo WARNING: Toolkit classifier step failed. Continuing.
  ) else (
    echo Toolkit classifier completed.
  )
) else (
  echo WARNING: Toolkit runner not found. Skipping.
)

echo.
echo ============================================================
echo   Running Unification Audit Extract
echo ============================================================
if /I "%ANALYTICS_RUN_UNIFICATION_AUDIT%"=="0" (
  echo Unification audit disabled by ANALYTICS_RUN_UNIFICATION_AUDIT=0
) else if exist "%ANALYTICS_AUDIT_SCRIPT%" (
  "%ANALYTICS_PYTHON%" "%ANALYTICS_AUDIT_SCRIPT%" --vault "%ANALYTICS_VAULT%" --out "%ANALYTICS_AUDIT_OUTPUT%"
  if errorlevel 1 (
    echo WARNING: Unification audit step failed. Continuing.
  ) else (
    echo Unification audit completed.
  )
) else (
  echo WARNING: Audit script not found. Skipping.
)

echo.
echo ============================================================
echo   Analytics Complete!
echo ============================================================
echo.
echo Results available in:
echo   - %ANALYTICS_OUTPUT_PATH%
echo.

if not defined ANALYTICS_NO_OPEN if exist "%ANALYTICS_OUTPUT_PATH%" start "" "%ANALYTICS_OUTPUT_PATH%"

echo.
echo Done!
if not defined ANALYTICS_NO_PAUSE pause
