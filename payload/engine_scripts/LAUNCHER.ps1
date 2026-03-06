# LAUNCHER.ps1 - Unified Script Menu for 01_ENGINE
# Provides organized access to all PowerShell, Python, and Batch scripts

$ErrorActionPreference = 'Stop'
$enginePath = Split-Path -Parent $MyInvocation.MyCommand.Path

function Show-Menu {
    Clear-Host
    Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Cyan
    Write-Host "         01_ENGINE UNIFIED SCRIPT LAUNCHER              " -ForegroundColor Yellow
    Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "MAIN APPLICATIONS" -ForegroundColor Green
    Write-Host "  1. Launch Vault App (GUI)" -ForegroundColor White
    Write-Host "  2. Launch Backend Server (app_v2.py)" -ForegroundColor White
    Write-Host "  3. Launch Vault Rater" -ForegroundColor White
    Write-Host ""
    Write-Host "TESTING & VALIDATION" -ForegroundColor Green
    Write-Host "  4. Run All Tests" -ForegroundColor White
    Write-Host "  5. Test Backend Only" -ForegroundColor White
    Write-Host "  6. Test Frontend Only" -ForegroundColor White
    Write-Host "  7. Test OpenAI Integration" -ForegroundColor White
    Write-Host "  8. Test Edge-TTS" -ForegroundColor White
    Write-Host ""
    Write-Host "DATA & ANALYTICS" -ForegroundColor Green
    Write-Host "  9. Vault Analytics Dashboard" -ForegroundColor White
    Write-Host " 10. Generate Vault Report" -ForegroundColor White
    Write-Host " 11. Export Data" -ForegroundColor White
    Write-Host ""
    Write-Host "VAULT & CONTENT" -ForegroundColor Green
    Write-Host " 12. Vault Tools (VaultTools.ps1)" -ForegroundColor White
    Write-Host " 13. Content Processor" -ForegroundColor White
    Write-Host " 14. Batch Content Tools" -ForegroundColor White
    Write-Host " 15. Link Analyzer" -ForegroundColor White
    Write-Host " 16. Tag Manager" -ForegroundColor White
    Write-Host ""
    Write-Host "BACKUP & MAINTENANCE" -ForegroundColor Green
    Write-Host " 17. Create Backup" -ForegroundColor White
    Write-Host " 18. Verify Integrity" -ForegroundColor White
    Write-Host " 19. Clean Temp Files" -ForegroundColor White
    Write-Host ""
    Write-Host "OPENAI TOOLS" -ForegroundColor Green
    Write-Host " 20. OpenAI Axiom Tool" -ForegroundColor White
    Write-Host " 21. OpenAI Context Manager" -ForegroundColor White
    Write-Host " 22. OpenAI Embedding Generator" -ForegroundColor White
    Write-Host " 23. OpenAI Response Parser" -ForegroundColor White
    Write-Host " 24. OpenAI Batch Processor" -ForegroundColor White
    Write-Host " 25. OpenAI Token Counter" -ForegroundColor White
    Write-Host ""
    Write-Host "ADVANCED" -ForegroundColor Green
    Write-Host " 26. Database Tools (05.ps1)" -ForegroundColor White
    Write-Host " 27. Sync Tools (06.ps1)" -ForegroundColor White
    Write-Host " 28. Analysis Tools (07.ps1)" -ForegroundColor White
    Write-Host " 29. Run Custom Python Script" -ForegroundColor White
    Write-Host " 30. Run Custom PowerShell Script" -ForegroundColor White
    Write-Host ""
    Write-Host "  Q. Quit" -ForegroundColor Red
    Write-Host ""
}

function Launch-Script {
    param(
        [string]$ScriptName,
        [string]$ScriptType,
        [string]$Description
    )
    
    $scriptPath = Join-Path $enginePath $ScriptName
    
    if (-not (Test-Path $scriptPath)) {
        Write-Host "ERROR: Script not found: $scriptPath" -ForegroundColor Red
        return
    }
    
    Write-Host "`nLaunching: $Description" -ForegroundColor Cyan
    Write-Host "Path: $scriptPath" -ForegroundColor Gray
    
    try {
        switch ($ScriptType) {
            'PowerShell' {
                & powershell.exe -NoExit -File $scriptPath
            }
            'Python' {
                & python $scriptPath
            }
            'Batch' {
                & cmd.exe /c $scriptPath
            }
        }
    } catch {
        Write-Host "ERROR: Failed to launch script: $_" -ForegroundColor Red
    }
}

# Main Loop
do {
    Show-Menu
    $choice = Read-Host "Select option (1-30 or Q)"
    
    switch ($choice) {
        '1'  { Launch-Script "scripts\python_pipeline\main.py" "Python" "Vault App GUI" }
        '2'  { Launch-Script "scripts\python_pipeline\app_v2.py" "Python" "Backend Server" }
        '3'  { Launch-Script "scripts\python_pipeline\vault_rater.py" "Python" "Vault Rater" }
        
        '4'  { Launch-Script "scripts\python_pipeline\testing\run_all_tests.bat" "Batch" "All Tests" }
        '5'  { Launch-Script "scripts\python_pipeline\testing\test_backend_only.bat" "Batch" "Backend Tests" }
        '6'  { Launch-Script "scripts\python_pipeline\testing\test_frontend_only.bat" "Batch" "Frontend Tests" }
        '7'  { Launch-Script "scripts\python_pipeline\testing\test_openai.bat" "Batch" "OpenAI Integration Test" }
        '8'  { Launch-Script "scripts\python_pipeline\testing\test_edge_tts.bat" "Batch" "Edge-TTS Test" }
        
        '9'  { Launch-Script "scripts\python_pipeline\analytics\dashboard.py" "Python" "Analytics Dashboard" }
        '10' { Launch-Script "scripts\python_pipeline\analytics\generate_report.py" "Python" "Vault Report Generator" }
        '11' { Launch-Script "scripts\python_pipeline\utils\export_data.py" "Python" "Data Exporter" }
        
        '12' { Launch-Script "VaultTools.ps1" "PowerShell" "Vault Tools" }
        '13' { Launch-Script "scripts\python_pipeline\processors\content_processor.py" "Python" "Content Processor" }
        '14' { Launch-Script "scripts\python_pipeline\batch_tools\batch_content.bat" "Batch" "Batch Content Tools" }
        '15' { Launch-Script "scripts\python_pipeline\analyzers\link_analyzer.py" "Python" "Link Analyzer" }
        '16' { Launch-Script "scripts\python_pipeline\utils\tag_manager.py" "Python" "Tag Manager" }
        
        '17' { Launch-Script "scripts\python_pipeline\maintenance\create_backup.py" "Python" "Backup Creator" }
        '18' { Launch-Script "scripts\python_pipeline\maintenance\verify_integrity.py" "Python" "Integrity Verifier" }
        '19' { Launch-Script "scripts\python_pipeline\maintenance\clean_temp.bat" "Batch" "Temp File Cleaner" }
        
        '20' { Launch-Script "scripts\python_pipeline\openai_tools\axiom_tool.bat" "Batch" "OpenAI Axiom Tool" }
        '21' { Launch-Script "scripts\python_pipeline\openai_tools\context_manager.bat" "Batch" "OpenAI Context Manager" }
        '22' { Launch-Script "scripts\python_pipeline\openai_tools\embedding_generator.bat" "Batch" "OpenAI Embedding Generator" }
        '23' { Launch-Script "scripts\python_pipeline\openai_tools\response_parser.bat" "Batch" "OpenAI Response Parser" }
        '24' { Launch-Script "scripts\python_pipeline\openai_tools\batch_processor.bat" "Batch" "OpenAI Batch Processor" }
        '25' { Launch-Script "scripts\python_pipeline\openai_tools\token_counter.bat" "Batch" "OpenAI Token Counter" }
        
        '26' { Launch-Script "05.ps1" "PowerShell" "Database Tools" }
        '27' { Launch-Script "06.ps1" "PowerShell" "Sync Tools" }
        '28' { Launch-Script "07.ps1" "PowerShell" "Analysis Tools" }
        '29' {
            $customScript = Read-Host "Enter Python script name (relative to ENGINE folder)"
            Launch-Script $customScript "Python" "Custom Python Script"
        }
        '30' {
            $customScript = Read-Host "Enter PowerShell script name (relative to ENGINE folder)"
            Launch-Script $customScript "PowerShell" "Custom PowerShell Script"
        }
        
        'Q' { 
            Write-Host "`nExiting launcher..." -ForegroundColor Yellow
            break
        }
        
        default {
            Write-Host "`nInvalid selection. Press any key to continue..." -ForegroundColor Red
            $null = $Host.UI.RawUI.ReadKey('NoEcho,IncludeKeyDown')
        }
    }
    
    if ($choice -ne 'Q') {
        Write-Host "`nPress any key to return to menu..." -ForegroundColor Gray
        $null = $Host.UI.RawUI.ReadKey('NoEcho,IncludeKeyDown')
    }
} while ($choice -ne 'Q')
