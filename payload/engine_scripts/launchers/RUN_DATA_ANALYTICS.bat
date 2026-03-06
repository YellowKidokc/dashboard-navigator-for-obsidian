@echo off
setlocal enabledelayedexpansion
title Theophysics Data Analytics Launcher

REM ============================================================
REM  THEOPHYSICS DATA ANALYTICS LAUNCHER
REM  Engine Room Script - One-click analytics pipeline
REM ============================================================

REM Paths
set ANALYTICS_ENGINE=O:\999_IGNORE\Obsidian Data Analytics\02_Python_Engine
set OUTPUT_PATH=O:\_Theophysics\999_Exclude\Obsidian Data Analytics\03_Dashboards
set VAULT_PATH=O:\_Theophysics_v3

REM Colors and formatting
color 0B

:MENU
cls
echo.
echo  ============================================================
echo       THEOPHYSICS DATA ANALYTICS LAUNCHER
echo  ============================================================
echo.
echo   Vault:   %VAULT_PATH%
echo   Engine:  %ANALYTICS_ENGINE%
echo   Output:  %OUTPUT_PATH%
echo.
echo  ============================================================
echo.
echo   [1]  RUN COMPLETE PIPELINE (All 11 Steps)
echo        Local stats + Global + Axioms + Theology + Math
echo        + Excel (10 workbooks) + HTML (6 dashboards)
echo        + Deep Metrics + Executive Summary
echo.
echo   [2]  Deep Metrics Only (50 metrics per paper)
echo        Scans Logos papers P01-P14, outputs 7 JSON files
echo.
echo   [3]  Excel + HTML Only (from existing data)
echo        Generates 10 Excel workbooks + 6 HTML dashboards
echo.
echo   [4]  Executive Summary Only
echo        Generates EXECUTIVE_SUMMARY.md from all data
echo.
echo   [5]  ANALYZE CUSTOM FOLDER
echo        Point at any folder of .md files
echo        Runs deep metrics + Excel + HTML + Summary
echo        Copies all results INTO the source folder
echo.
echo   [6]  Open Output Folder
echo.
echo   [7]  Open Command Center GUI
echo.
echo   [0]  Exit
echo.
echo  ============================================================
echo.

set /p CHOICE="  Select option [0-7]: "

if "%CHOICE%"=="1" goto FULL_PIPELINE
if "%CHOICE%"=="2" goto DEEP_METRICS
if "%CHOICE%"=="3" goto EXCEL_HTML
if "%CHOICE%"=="4" goto EXEC_SUMMARY
if "%CHOICE%"=="5" goto CUSTOM_FOLDER
if "%CHOICE%"=="6" goto OPEN_FOLDER
if "%CHOICE%"=="7" goto COMMAND_CENTER
if "%CHOICE%"=="0" goto EXIT

echo  Invalid choice. Try again.
timeout /t 2 >nul
goto MENU

:FULL_PIPELINE
cls
echo.
echo  ============================================================
echo   RUNNING COMPLETE ANALYTICS PIPELINE (11 Steps)
echo  ============================================================
echo.
echo  This will:
echo    - Scan all vault notes for local statistics
echo    - Generate global analytics
echo    - Run axiom, theology, and math analysis
echo    - Generate 10 Excel workbooks
echo    - Generate 6 HTML dashboards
echo    - Run 50-metric deep analysis on Logos papers
echo    - Generate executive summary
echo.
echo  Estimated time: 5-15 minutes depending on vault size
echo.
set /p CONFIRM="  Proceed? [Y/N]: "
if /i not "%CONFIRM%"=="Y" goto MENU

echo.
echo  Starting pipeline...
echo.

cd /d "%ANALYTICS_ENGINE%"
call RUN_COMPLETE_ANALYTICS.bat

echo.
echo  ============================================================
echo   PIPELINE COMPLETE
echo  ============================================================
echo.
echo  Output location: %OUTPUT_PATH%
echo.
echo  Generated:
echo    - 10 Excel workbooks in %OUTPUT_PATH%\Excel\
echo    - 6 HTML dashboards in %OUTPUT_PATH%\HTML\
echo    - 7 Deep metrics JSON in %OUTPUT_PATH%\DeepMetrics\
echo    - EXECUTIVE_SUMMARY.md
echo.
set /p OPEN="  Open output folder? [Y/N]: "
if /i "%OPEN%"=="Y" start "" "%OUTPUT_PATH%"
goto MENU

:DEEP_METRICS
cls
echo.
echo  ============================================================
echo   RUNNING DEEP BACKEND METRICS
echo  ============================================================
echo.
echo  Scanning Logos papers P01-P14 for 50 metrics each...
echo.

cd /d "%ANALYTICS_ENGINE%"
python generate_deep_metrics.py
if errorlevel 1 (
    echo.
    echo  ERROR: Deep metrics failed. Check Python dependencies.
    pause
    goto MENU
)

echo.
echo  Deep metrics complete!
echo.

REM Ask if they want dashboards too
set /p DASH="  Also generate deep dashboards? [Y/N]: "
if /i "%DASH%"=="Y" (
    echo.
    python generate_deep_dashboards.py
    echo.
    echo  Dashboard saved to: %OUTPUT_PATH%\HTML\deep_metrics_dashboard.html
)

echo.
set /p OPEN="  Open output folder? [Y/N]: "
if /i "%OPEN%"=="Y" start "" "%OUTPUT_PATH%\DeepMetrics"
goto MENU

:EXCEL_HTML
cls
echo.
echo  ============================================================
echo   GENERATING EXCEL + HTML FROM EXISTING DATA
echo  ============================================================
echo.

cd /d "%ANALYTICS_ENGINE%"

echo  [1/3] Generating 10 Excel workbooks...
python export_to_excel.py
echo.

echo  [2/3] Generating 5 HTML dashboards...
python generate_html_dashboards.py
echo.

echo  [3/3] Generating deep Plotly dashboard...
python generate_deep_dashboards.py
echo.

echo  ============================================================
echo   EXPORT COMPLETE
echo  ============================================================
echo.
echo  Excel: %OUTPUT_PATH%\Excel\
echo  HTML:  %OUTPUT_PATH%\HTML\
echo.
set /p OPEN="  Open output folder? [Y/N]: "
if /i "%OPEN%"=="Y" start "" "%OUTPUT_PATH%\Excel"
goto MENU

:EXEC_SUMMARY
cls
echo.
echo  ============================================================
echo   GENERATING EXECUTIVE SUMMARY
echo  ============================================================
echo.

cd /d "%ANALYTICS_ENGINE%"
python generate_llm_summary.py

echo.
echo  Summary saved to: %OUTPUT_PATH%\EXECUTIVE_SUMMARY.md
echo.
set /p OPEN="  Open summary? [Y/N]: "
if /i "%OPEN%"=="Y" start "" "%OUTPUT_PATH%\EXECUTIVE_SUMMARY.md"
goto MENU

:CUSTOM_FOLDER
cls
echo.
echo  ============================================================
echo   ANALYZE CUSTOM FOLDER
echo  ============================================================
echo.
echo  Enter the full path to a folder containing .md files.
echo  All analytics will run and results will be copied INTO
echo  a _Data_Analytics subfolder of that folder.
echo.
echo  Example: O:\_Theophysics_v3\02_THEOPHYSICS\3_Truths
echo.
set /p FOLDER_PATH="  Folder path: "

if "%FOLDER_PATH%"=="" (
    echo  No path entered.
    pause
    goto MENU
)

if not exist "%FOLDER_PATH%" (
    echo.
    echo  ERROR: Folder not found: %FOLDER_PATH%
    pause
    goto MENU
)

REM Extract folder name for labeling
for %%F in ("%FOLDER_PATH%") do set FOLDER_NAME=%%~nxF

echo.
echo  Target folder: %FOLDER_PATH%
echo  Folder label:  %FOLDER_NAME%
echo.
echo  This will:
echo    1. Run 50-metric deep analysis on all .md files
echo    2. Generate Plotly HTML dashboard
echo    3. Generate 3 Excel workbooks
echo    4. Generate executive summary
echo    5. Copy ALL results into %FOLDER_PATH%\_Data_Analytics\
echo.
set /p CONFIRM="  Proceed? [Y/N]: "
if /i not "%CONFIRM%"=="Y" goto MENU

echo.
echo  ============================================================
echo   STEP 1/4: Running Deep Metrics on %FOLDER_NAME%...
echo  ============================================================
echo.

cd /d "%ANALYTICS_ENGINE%"
python generate_deep_metrics.py --folder "%FOLDER_PATH%"
if errorlevel 1 (
    echo.
    echo  ERROR: Deep metrics failed.
    pause
    goto MENU
)

echo.
echo  ============================================================
echo   STEP 2/4: Generating Plotly Dashboard...
echo  ============================================================
echo.

python generate_deep_dashboards.py --folder "%FOLDER_NAME%"
if errorlevel 1 (
    echo  WARNING: Dashboard generation had issues, continuing...
)

echo.
echo  ============================================================
echo   STEP 3/4: Generating Excel Workbooks...
echo  ============================================================
echo.

python export_to_excel.py --folder "%FOLDER_NAME%"
if errorlevel 1 (
    echo  WARNING: Excel export had issues, continuing...
)

echo.
echo  ============================================================
echo   STEP 4/4: Generating Executive Summary...
echo  ============================================================
echo.

python generate_llm_summary.py --folder "%FOLDER_NAME%"
if errorlevel 1 (
    echo  WARNING: Summary generation had issues, continuing...
)

echo.
echo  ============================================================
echo   CUSTOM FOLDER ANALYSIS COMPLETE!
echo  ============================================================
echo.
echo  Source:  %FOLDER_PATH%
echo  Results: %FOLDER_PATH%\_Data_Analytics\
echo.
echo  Generated:
echo    - 7 JSON metric files
echo    - 3 Excel workbooks
echo    - 1 Interactive HTML dashboard
echo    - 1 Executive summary (MD)
echo.
echo  All results copied to: %FOLDER_PATH%\_Data_Analytics\
echo.
set /p OPEN="  Open results folder? [Y/N]: "
if /i "%OPEN%"=="Y" start "" "%FOLDER_PATH%\_Data_Analytics"
goto MENU

:OPEN_FOLDER
start "" "%OUTPUT_PATH%"
goto MENU

:COMMAND_CENTER
echo.
echo  Launching Command Center GUI...
cd /d "O:\999_IGNORE\Obsidian Programs\Python_Backend\analytics"
start "" python THEOPHYSICS_COMMAND_CENTER.py
goto MENU

:EXIT
echo.
echo  Goodbye!
echo.
exit /b 0
