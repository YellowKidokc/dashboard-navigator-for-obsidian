# ============================================================
#  THEOPHYSICS MASTER TOOLS MENU
#  Drop _TOOLS.bat in any vault folder — double-click to run
#  Context folder (where you launched from) is passed in as arg
# ============================================================

param(
    [string]$ContextFolder = ""
)

$Host.UI.RawUI.WindowTitle = "Theophysics Tools"
$ErrorActionPreference = "SilentlyContinue"

$SCRIPT_DIR  = Split-Path -Parent $MyInvocation.MyCommand.Path
$VAULT_EXCEL = "C:\Users\lowes\OneDrive\Desktop\Master Theophysics Obsidian VAULT.xlsx"
$IMPORTER    = Join-Path $SCRIPT_DIR "vault_score_importer.py"
$LOG_FILE    = "C:\Users\lowes\OneDrive\Desktop\vault_import_log.txt"
$TTS_DIR     = Join-Path (Split-Path -Parent $SCRIPT_DIR) "TTS_Pipeline"

# Use context folder or fall back to script dir
if ([string]::IsNullOrWhiteSpace($ContextFolder) -or !(Test-Path $ContextFolder)) {
    $ContextFolder = $SCRIPT_DIR
}

# ── Colors ────────────────────────────────────────────────────
function Write-Header  { param($t) Write-Host "`n  $t" -ForegroundColor Cyan }
function Write-OK      { param($t) Write-Host "  [OK] $t" -ForegroundColor Green }
function Write-Err     { param($t) Write-Host "  [!!] $t" -ForegroundColor Red }
function Write-Info    { param($t) Write-Host "  [>>] $t" -ForegroundColor Yellow }
function Write-Divider { Write-Host "  ------------------------------------------------------------" -ForegroundColor DarkGray }

# ── Helpers ───────────────────────────────────────────────────
function Pick-Folder([string]$Default) {
    Add-Type -AssemblyName System.Windows.Forms
    $dlg = New-Object System.Windows.Forms.FolderBrowserDialog
    $dlg.Description = "Select vault folder"
    $dlg.SelectedPath = $Default
    if ($dlg.ShowDialog() -eq "OK") { return $dlg.SelectedPath }
    return $null
}

function Check-Python {
    try {
        $v = python --version 2>&1
        if ($v -match "Python") { return $true }
    } catch {}
    Write-Err "Python not found. Install Python 3.8+"
    return $false
}

function Open-Excel {
    if (Test-Path $VAULT_EXCEL) {
        Start-Process $VAULT_EXCEL
        Write-OK "Opened: $VAULT_EXCEL"
    } else {
        Write-Err "Not found: $VAULT_EXCEL"
    }
}

# ── Score Import functions ─────────────────────────────────────
function Import-Scores([string]$Folder, [bool]$Clean) {
    Clear-Host
    $label = if ($Clean) { "IMPORT + CLEAN" } else { "IMPORT SCORES" }
    Write-Header $label
    Write-Divider
    Write-Info "Folder : $Folder"
    Write-Info "Clean  : $Clean"
    Write-Host ""

    if (!(Check-Python)) { pause; return }
    if (!(Test-Path $IMPORTER)) { Write-Err "Importer script not found: $IMPORTER"; pause; return }

    # Check if Excel is open
    $lockFile = [System.IO.Path]::Combine(
        [System.IO.Path]::GetDirectoryName($VAULT_EXCEL),
        "~`$" + [System.IO.Path]::GetFileName($VAULT_EXCEL)
    )
    if (Test-Path $lockFile) {
        Write-Err "Master Vault Excel is open. Please close it first."
        Write-Host ""
        $open = Read-Host "  Open Excel so you can close it? (Y/N)"
        if ($open -eq "Y") { Open-Excel }
        pause
        return
    }

    Write-Info "Running importer..."
    Write-Host ""

    if ($Clean) {
        python $IMPORTER $Folder --clean
    } else {
        python $IMPORTER $Folder
    }

    Write-Host ""
    if (Test-Path $LOG_FILE) {
        Write-OK "Log saved to Desktop: vault_import_log.txt"
        $show = Read-Host "  View log? (Y/N)"
        if ($show -eq "Y") { Get-Content $LOG_FILE | More }
    }

    Write-Host ""
    $openEx = Read-Host "  Open Master Excel now? (Y/N)"
    if ($openEx -eq "Y") { Open-Excel }
    pause
}

# ── OpenAI sub-menu ───────────────────────────────────────────
function Launch-OpenAI {
    $openaiMenu = Join-Path $SCRIPT_DIR "OPENAI_MENU.ps1"
    if (Test-Path $openaiMenu) {
        & $openaiMenu
    } else {
        Write-Err "OpenAI menu not found: $openaiMenu"
        pause
    }
}

# ── VaultTools sub-menu ───────────────────────────────────────
function Launch-VaultTools {
    $vtMenu = Join-Path $SCRIPT_DIR "VaultTools.ps1"
    if (Test-Path $vtMenu) {
        & $vtMenu
    } else {
        Write-Err "VaultTools not found: $vtMenu"
        pause
    }
}

# ── TTS Pipeline helpers ──────────────────────────────────────
function Launch-TTS([string]$BatName) {
    $bat = Join-Path $TTS_DIR $BatName
    if (!(Test-Path $bat)) {
        Write-Err "Not found: $bat"
        Write-Info "Run SETUP first (option 8) to install the TTS Pipeline."
        pause
        return
    }
    Start-Process "cmd.exe" -ArgumentList "/c `"$bat`"" -WorkingDirectory $TTS_DIR
    Write-OK "Launched: $BatName"
    Start-Sleep 1
}

function Launch-TTS-Setup {
    $bat = Join-Path $TTS_DIR "SETUP.bat"
    if (!(Test-Path $bat)) { Write-Err "SETUP.bat not found: $bat"; pause; return }
    Start-Process "cmd.exe" -ArgumentList "/c `"$bat`"" -WorkingDirectory $TTS_DIR -Wait
}

function Open-TTS-Inbox {
    $inbox = Join-Path $TTS_DIR "INBOX"
    if (!(Test-Path $inbox)) { New-Item -ItemType Directory -Path $inbox | Out-Null }
    Start-Process "explorer.exe" $inbox
    Write-OK "Opened INBOX: $inbox"
    Start-Sleep 1
}

# ── UTQS Scorer ───────────────────────────────────────────────
function Launch-UTQS {
    $utqsBat = Join-Path $SCRIPT_DIR "run_utqs_excel.bat"
    if (Test-Path $utqsBat) {
        Start-Process "cmd.exe" -ArgumentList "/c `"$utqsBat`"" -WorkingDirectory $SCRIPT_DIR -Wait
    } else {
        Write-Err "run_utqs_excel.bat not found: $utqsBat"
        pause
    }
}

# ── View Log ──────────────────────────────────────────────────
function View-Log {
    Clear-Host
    Write-Header "LAST IMPORT LOG"
    Write-Divider
    if (Test-Path $LOG_FILE) {
        Get-Content $LOG_FILE | More
    } else {
        Write-Info "No log file found yet."
    }
    Write-Host ""
    pause
}

# ── Main Menu Loop ────────────────────────────────────────────
while ($true) {
    Clear-Host
    Write-Host ""
    Write-Host "  ============================================================" -ForegroundColor Cyan
    Write-Host "    THEOPHYSICS MASTER TOOLS" -ForegroundColor Cyan
    Write-Host "  ============================================================" -ForegroundColor Cyan
    Write-Host "  Context: " -NoNewline -ForegroundColor DarkGray
    Write-Host $ContextFolder -ForegroundColor White
    Write-Host "  Excel  : " -NoNewline -ForegroundColor DarkGray
    if (Test-Path $VAULT_EXCEL) {
        Write-Host "FOUND" -ForegroundColor Green
    } else {
        Write-Host "NOT FOUND" -ForegroundColor Red
    }
    Write-Host ""
    Write-Host "  SCORE IMPORT" -ForegroundColor Yellow
    Write-Host "    1.  Import scores from THIS folder  -> Master Excel" -ForegroundColor White
    Write-Host "    2.  Import scores + delete CSV files (THIS folder)" -ForegroundColor White
    Write-Host "    3.  Pick a different folder to import from" -ForegroundColor White
    Write-Host ""
    Write-Host "  EXCEL" -ForegroundColor Yellow
    Write-Host "    4.  Open Master Excel on Desktop" -ForegroundColor White
    Write-Host "    5.  View last import log" -ForegroundColor White
    Write-Host ""
    Write-Host "  TTS PIPELINE" -ForegroundColor Yellow
    Write-Host "    8.  Setup TTS Pipeline  (first-time install)" -ForegroundColor White
    Write-Host "    9.  Open INBOX folder   (drop .md files here)" -ForegroundColor White
    Write-Host "    10. Batch TTS           (.md -> audio)" -ForegroundColor White
    Write-Host "    11. Paper Formatter     (equation translation GUI)" -ForegroundColor White
    Write-Host "    12. Math Translation    (batch math-to-prose GUI)" -ForegroundColor White
    Write-Host "    13. Substack Publisher  (OUTBOX -> HTML for Substack)" -ForegroundColor White
    Write-Host "    14. Google Drive Upload (upload + insert links)" -ForegroundColor White
    Write-Host ""
    Write-Host "  OTHER TOOLS" -ForegroundColor Yellow
    Write-Host "    6.  OpenAI Tools  (CKG / Domain / Decompress)" -ForegroundColor White
    Write-Host "    7.  Vault Tools   (Renumber / Split / Group files)" -ForegroundColor White
    Write-Host "    15. UTQS Scorer   (Quality score a paper workbook)" -ForegroundColor White
    Write-Host ""
    Write-Host "    0.  Exit" -ForegroundColor DarkGray
    Write-Host ""
    Write-Host "  ============================================================" -ForegroundColor Cyan

    $choice = (Read-Host "`n  Select").Trim()

    switch ($choice) {
        "1"  { Import-Scores -Folder $ContextFolder -Clean $false }
        "2"  { Import-Scores -Folder $ContextFolder -Clean $true  }
        "3"  {
                $picked = Pick-Folder -Default $ContextFolder
                if ($picked) {
                    $ContextFolder = $picked
                    Import-Scores -Folder $ContextFolder -Clean $false
                }
              }
        "4"  { Open-Excel; pause }
        "5"  { View-Log }
        "6"  { Launch-OpenAI }
        "7"  { Launch-VaultTools }
        "8"  { Launch-TTS-Setup }
        "9"  { Open-TTS-Inbox }
        "10" { Launch-TTS "LAUNCH_BATCH_TTS.bat" }
        "11" { Launch-TTS "LAUNCH_PAPER_FORMATTER.bat" }
        "12" { Launch-TTS "LAUNCH_MATH_TRANSLATION_MANAGER.bat" }
        "13" { Launch-TTS "LAUNCH_SUBSTACK_BATCH.bat" }
        "14" { Launch-TTS "LAUNCH_GDRIVE_UPLOAD.bat" }
        "15" { Launch-UTQS }
        "0"  { exit }
        default { Write-Host "`n  Invalid option" -ForegroundColor Red; Start-Sleep 1 }
    }
}
