@echo off
setlocal enabledelayedexpansion
REM ============================================================
REM  FOLDER MENU — Universal Vault Operations
REM  Drop this bat in any folder, or run with a folder path.
REM  Usage: folder_menu.bat [FOLDER_PATH]
REM ============================================================

set "SCRIPTS_DIR=O:\_Theophysics_v3\00_SYSTEM\01_ENGINE\scripts"
set "VAULT_ROOT=O:\_Theophysics_v3"

REM Determine target folder
if "%~1"=="" (
    set "TARGET=%CD%"
) else (
    set "TARGET=%~1"
)

:menu
cls
echo.
echo ========================================================
echo   VAULT FOLDER MENU
echo ========================================================
echo   Target: %TARGET%
echo ========================================================
echo.
echo   --- Navigation ---
echo   1) Build MOC for this folder
echo   2) Build MOCs for this folder + all subfolders
echo   3) Open folder in Explorer
echo.
echo   --- Cleanup ---
echo   4) Scan encoding issues (dry run)
echo   5) Fix encoding issues (CRLF, BOM, nulls, invisible)
echo   6) Clean filenames (trim spaces)
echo.
echo   --- Analysis ---
echo   7) Health check (broken links, orphans, stats)
echo   8) Find bloat files (large/binary)
echo   9) Summarize papers in this folder
echo.
echo   --- File Operations ---
echo   10) Renumber files (Name_01_of_N.ext)
echo   11) Split a large text file (2-10 parts)
echo   12) Group files into batches
echo   13) Combine all markdown files into one
echo.
echo   --- Vault-Wide ---
echo   14) Full vault rebuild (all MOCs + dashboards)
echo   15) Papers dashboard only
echo   16) Scripts dashboard
echo   17) Vault health report
echo.
echo   C) Change target folder
echo   Q) Quit
echo.
set /p choice="  Select: "

if /i "%choice%"=="Q" goto :eof
if /i "%choice%"=="C" goto :changefolder

if "%choice%"=="1" goto :moc_single
if "%choice%"=="2" goto :moc_recursive
if "%choice%"=="3" goto :open_explorer
if "%choice%"=="4" goto :clean_scan
if "%choice%"=="5" goto :clean_fix
if "%choice%"=="6" goto :clean_filenames
if "%choice%"=="7" goto :health
if "%choice%"=="8" goto :bloat
if "%choice%"=="9" goto :summarize
if "%choice%"=="10" goto :renumber
if "%choice%"=="11" goto :split
if "%choice%"=="12" goto :group
if "%choice%"=="13" goto :combine
if "%choice%"=="14" goto :full_rebuild
if "%choice%"=="15" goto :papers_dash
if "%choice%"=="16" goto :scripts_dash
if "%choice%"=="17" goto :vault_health

echo Unknown selection.
pause
goto :menu

:moc_single
echo.
echo Building MOC for: %TARGET%
python "%SCRIPTS_DIR%\vault_navigator.py" --folder "%TARGET%" --vault "%VAULT_ROOT%"
pause
goto :menu

:moc_recursive
echo.
echo Building MOCs for folder tree: %TARGET%
python "%SCRIPTS_DIR%\vault_navigator.py" --mocs-only --vault "%TARGET%"
pause
goto :menu

:open_explorer
explorer "%TARGET%"
goto :menu

:clean_scan
echo.
echo Scanning encoding issues (dry run)...
python "%SCRIPTS_DIR%\vault_toolkit.py" clean "%TARGET%"
pause
goto :menu

:clean_fix
echo.
echo Fixing encoding issues...
python "%SCRIPTS_DIR%\vault_toolkit.py" clean --fix "%TARGET%"
pause
goto :menu

:clean_filenames
echo.
echo Fixing filenames...
python "%SCRIPTS_DIR%\vault_toolkit.py" clean --fix --filenames "%TARGET%"
pause
goto :menu

:health
echo.
echo Running health check...
python "%SCRIPTS_DIR%\vault_toolkit.py" health "%TARGET%"
pause
goto :menu

:bloat
echo.
echo Finding bloat files...
python "%SCRIPTS_DIR%\vault_toolkit.py" bloat "%TARGET%"
pause
goto :menu

:summarize
echo.
echo Summarizing papers in: %TARGET%
python "%SCRIPTS_DIR%\vault_navigator.py" --papers-only --vault "%VAULT_ROOT%"
pause
goto :menu

:renumber
echo.
echo Launching VaultTools renumber...
powershell -NoProfile -ExecutionPolicy Bypass -Command "& { Set-Location '%TARGET%'; . '%SCRIPTS_DIR%\VaultTools.ps1' }"
pause
goto :menu

:split
echo.
set /p splitfile="  Full path to file: "
set /p splitparts="  How many parts (2-10): "
powershell -NoProfile -ExecutionPolicy Bypass -Command "& { . '%SCRIPTS_DIR%\VaultTools.ps1'; Split-TextFile -FilePath '%splitfile%' -Parts %splitparts% }"
pause
goto :menu

:group
echo.
set /p groupsize="  Group size: "
powershell -NoProfile -ExecutionPolicy Bypass -Command "& { . '%SCRIPTS_DIR%\VaultTools.ps1'; Group-Files -Dir '%TARGET%' -GroupSize %groupsize% -MakeFolders }"
pause
goto :menu

:combine
echo.
echo Combining all .md files in: %TARGET%
set "OUTFILE=%TARGET%\COMBINED_MARKDOWN.md"
echo --- > "%OUTFILE%"
echo type: combined >> "%OUTFILE%"
echo generated: %DATE% %TIME% >> "%OUTFILE%"
echo source: %TARGET% >> "%OUTFILE%"
echo --- >> "%OUTFILE%"
echo. >> "%OUTFILE%"
for %%f in ("%TARGET%\*.md") do (
    if not "%%~nxf"=="COMBINED_MARKDOWN.md" (
        if not "%%~nxf"=="_MOC.md" (
            echo # %%~nf >> "%OUTFILE%"
            echo. >> "%OUTFILE%"
            type "%%f" >> "%OUTFILE%"
            echo. >> "%OUTFILE%"
            echo --- >> "%OUTFILE%"
            echo. >> "%OUTFILE%"
        )
    )
)
echo Combined into: %OUTFILE%
pause
goto :menu

:full_rebuild
echo.
echo Full vault rebuild...
python "%SCRIPTS_DIR%\vault_navigator.py" --full --vault "%VAULT_ROOT%"
pause
goto :menu

:papers_dash
echo.
echo Generating Papers Dashboard...
python "%SCRIPTS_DIR%\vault_navigator.py" --papers-only --vault "%VAULT_ROOT%"
pause
goto :menu

:scripts_dash
echo.
echo Generating Scripts Dashboard...
python "%SCRIPTS_DIR%\generate_scripts_dashboard.py" --vault "%VAULT_ROOT%"
pause
goto :menu

:vault_health
echo.
echo Running vault health report...
python "%SCRIPTS_DIR%\vault_toolkit.py" health "%VAULT_ROOT%"
pause
goto :menu

:changefolder
echo.
set /p newfolder="  New folder path: "
if exist "%newfolder%" (
    set "TARGET=%newfolder%"
) else (
    echo Folder not found.
    pause
)
goto :menu
