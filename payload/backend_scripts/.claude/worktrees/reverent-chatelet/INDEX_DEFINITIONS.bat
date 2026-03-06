@echo off
REM ============================================
REM   DEFINITION ENGINE - Index & Check Drift
REM ============================================

echo.
echo ========================================
echo   THEOPHYSICS DEFINITION ENGINE
echo ========================================
echo.
echo This tool:
echo   1. Indexes all definitions in your vault
echo   2. Tracks where each term is used
echo   3. Maps equations to definitions
echo   4. Detects usage drift
echo.

REM Install dependencies
pip install pyyaml requests beautifulsoup4 --quiet

set /p vault="Enter vault path (or press Enter for current): "
if "%vault%"=="" set vault=.

echo.
echo Indexing vault: %vault%
echo.

python engine\enhanced_definition_engine.py "%vault%"

echo.
pause
