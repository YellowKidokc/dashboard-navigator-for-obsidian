@echo off
echo ============================================
echo OVERNIGHT MATH TRANSLATION PROCESSOR
echo ============================================
echo.
echo This will process all equations in your papers
echo using Ollama (FREE, local inference).
echo.
echo Make sure Ollama is running: ollama serve
echo.

cd /d "O:\Theophysics_Backend\Python_Backend\Backend Python"
call venv\Scripts\activate

python run_overnight_math.py

echo.
echo Processing complete!
pause
