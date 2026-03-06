@echo off
echo ========================================
echo THEOPHYSICS FULL ANALYTICS SUITE
echo ========================================
echo.
echo Running comprehensive analytics...
echo.

cd /d "%~dp0"

echo [1/6] Running corpus statistics...
python theophysics_stats.py
echo.

echo [2/6] Running paper analysis...
python logos_paper_analysis.py
echo.

echo [3/6] Running experimental stats...
python experimental_stats.py
echo.

echo [4/6] Running axiom coherence scorer...
python axiom_scorer.py
echo.

echo [5/6] Running external theories check...
python check_external.py
echo.

echo [6/6] Generating comprehensive dashboard...
python dashboard_aggregator.py
echo.

echo ========================================
echo COMPLETE!
echo ========================================
echo.
echo Check the Global_Analytics folder for output files.
pause
