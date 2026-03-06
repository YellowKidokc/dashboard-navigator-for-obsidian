@echo off
setlocal enabledelayedexpansion

:: ============================================================
::  NUMBER_FILES.bat — Auto-number files in a folder
:: ============================================================
::  Counts all files (including subfolders), sorts alphabetically,
::  renames each to:  01_of_51_Original_Filename.ext
::
::  Usage:
::    Drag a folder onto this script, OR
::    Run it and paste a folder path when prompted
::
::  Re-run safe: strips old numbering before re-numbering.
:: ============================================================

:: --- Get folder path ---
if "%~1"=="" (
    echo.
    echo  ========================================
    echo   FILE NUMBERER
    echo  ========================================
    echo.
    set /p "TARGET_DIR=  Paste folder path: "
) else (
    set "TARGET_DIR=%~1"
)

:: Remove quotes if user pasted them
set "TARGET_DIR=!TARGET_DIR:"=!"

:: Remove trailing backslash if present
if "!TARGET_DIR:~-1!"=="\" set "TARGET_DIR=!TARGET_DIR:~0,-1!"

:: Verify folder exists
if not exist "!TARGET_DIR!\" (
    echo.
    echo  ERROR: Folder not found: !TARGET_DIR!
    echo.
    pause
    exit /b 1
)

echo.
echo  Scanning: !TARGET_DIR!
echo  ----------------------------------------

:: --- Build sorted file list into temp file ---
set "TMPLIST=%TEMP%\numberfiles_%RANDOM%.txt"

:: List all files recursively, sorted by name, files only
dir /b /s /a-d /on "!TARGET_DIR!\*.*" > "!TMPLIST!" 2>nul

:: --- Count total files ---
set "TOTAL=0"
for /f "usebackq delims=" %%L in ("!TMPLIST!") do (
    set /a TOTAL+=1
)

if !TOTAL!==0 (
    echo.
    echo  No files found in that folder.
    del "!TMPLIST!" 2>nul
    pause
    exit /b 0
)

echo  Found: !TOTAL! files
echo.

:: --- Figure out zero-padding width ---
set "PAD=2"
if !TOTAL! GEQ 100 set "PAD=3"
if !TOTAL! GEQ 1000 set "PAD=4"

:: --- Zero-pad the total once ---
set "TOT=000!TOTAL!"
if !PAD!==2 set "TOT=!TOT:~-2!"
if !PAD!==3 set "TOT=!TOT:~-3!"
if !PAD!==4 set "TOT=!TOT:~-4!"

:: --- Sort alphabetically by filename and rename ---
:: We need to sort by filename only (not full path), so rebuild the list
set "TMPLIST2=%TEMP%\numberfiles2_%RANDOM%.txt"
(for /f "usebackq delims=" %%F in ("!TMPLIST!") do (
    echo %%~nxF|%%~dpF
)) > "!TMPLIST2!"

:: Sort by filename
set "TMPLIST3=%TEMP%\numberfiles3_%RANDOM%.txt"
sort "!TMPLIST2!" /o "!TMPLIST3!"

set "COUNT=0"
set "RENAMED=0"

for /f "usebackq tokens=1,* delims=|" %%A in ("!TMPLIST3!") do (
    set /a COUNT+=1
    set "FNAME=%%A"
    set "FDIR=%%B"

    :: Zero-pad the count
    set "NUM=000!COUNT!"
    if !PAD!==2 set "NUM=!NUM:~-2!"
    if !PAD!==3 set "NUM=!NUM:~-3!"
    if !PAD!==4 set "NUM=!NUM:~-4!"

    :: Check if already numbered — pattern: digits_of_digits_rest
    set "CLEAN=!FNAME!"
    set "CHECK=!FNAME:_of_=!"
    if not "!CHECK!"=="!FNAME!" (
        :: Contains _of_ — check if it starts with digits
        for /f "tokens=1,2,3,* delims=_" %%P in ("!FNAME!") do (
            if "%%Q"=="of" (
                :: Strip the old NN_of_NN_ prefix
                set "CLEAN=%%S"
            )
        )
    )

    set "NEWNAME=!NUM!_of_!TOT!_!CLEAN!"

    if not "!FNAME!"=="!NEWNAME!" (
        ren "!FDIR!!FNAME!" "!NEWNAME!" 2>nul
        if not errorlevel 1 (
            set /a RENAMED+=1
            echo   [!NUM!/!TOT!] !NEWNAME!
        ) else (
            echo   [!NUM!/!TOT!] SKIP: !FNAME! (rename failed^)
        )
    ) else (
        echo   [!NUM!/!TOT!] !NEWNAME! (unchanged^)
    )
)

:: Cleanup temp files
del "!TMPLIST!" 2>nul
del "!TMPLIST2!" 2>nul
del "!TMPLIST3!" 2>nul

echo.
echo  ========================================
echo   Done! !RENAMED! of !TOTAL! files renamed.
echo  ========================================
echo.
pause
