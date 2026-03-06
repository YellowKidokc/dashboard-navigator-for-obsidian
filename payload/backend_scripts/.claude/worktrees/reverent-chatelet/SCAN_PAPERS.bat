@echo off
REM ============================================
REM   KNOWLEDGE ACQUISITION SCANNER
REM   Scan papers, extract entities, link sources
REM ============================================

echo.
echo ========================================
echo   THEOPHYSICS KNOWLEDGE SCANNER
echo ========================================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found!
    pause
    exit /b 1
)

REM Install dependencies if needed
echo Installing dependencies...
pip install requests beautifulsoup4 markdownify pymupdf --quiet

echo.
echo Ready to scan papers and extract knowledge.
echo.
echo Options:
echo   1. Scan papers in current vault
echo   2. Scan a specific directory
echo   3. Test extraction on sample text
echo.

set /p choice="Enter choice (1-3): "

if "%choice%"=="1" (
    python -c "from engine.knowledge_acquisition_engine import *; import json; results = scan_papers_in_directory('.'); print(json.dumps(results['statistics'], indent=2))"
) else if "%choice%"=="2" (
    set /p dir="Enter directory path: "
    python -c "from engine.knowledge_acquisition_engine import *; import json; results = scan_papers_in_directory('%dir%'); print(json.dumps(results['statistics'], indent=2))"
) else if "%choice%"=="3" (
    python engine\knowledge_acquisition_engine.py
)

echo.
pause
