@echo off
echo ========================================
echo   OLLAMA OVERNIGHT YAML PROCESSOR
echo ========================================
echo.
echo This will process your vault with Ollama.
echo Make sure Ollama is running (ollama serve)
echo.
echo Options:
echo   1. Dry run (preview, no changes)
echo   2. Process all papers
echo   3. Process 10 files (test run)
echo   4. Skip files with existing frontmatter
echo.
set /p choice="Choose option (1-4): "

cd /d "O:\Theophysics_Backend\Backend Python"

if "%choice%"=="1" (
    echo.
    echo Running DRY RUN mode...
    python scripts\ollama_yaml_processor.py --dry-run
) else if "%choice%"=="2" (
    echo.
    echo Processing ALL papers...
    python scripts\ollama_yaml_processor.py
) else if "%choice%"=="3" (
    echo.
    echo Processing 10 files (test)...
    python scripts\ollama_yaml_processor.py --limit 10
) else if "%choice%"=="4" (
    echo.
    echo Processing only files WITHOUT frontmatter...
    python scripts\ollama_yaml_processor.py --skip-existing
) else (
    echo Invalid choice.
)

echo.
echo ========================================
echo   DONE
echo ========================================
pause
