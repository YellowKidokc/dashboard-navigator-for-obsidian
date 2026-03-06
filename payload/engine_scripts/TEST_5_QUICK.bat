@echo off
cd /d "O:\_Theophysics_v3\00_SYSTEM\01_ENGINE"
"C:\Users\lowes\AppData\Local\Programs\Python\Python313\python.exe" -c "import openai; print('openai:', openai.__version__)"
echo ---
"C:\Users\lowes\AppData\Local\Programs\Python\Python313\python.exe" vault_rater.py --pass 1 --limit 5 --skip-move --skip-frontmatter 2>&1
echo ---DONE---
pause
