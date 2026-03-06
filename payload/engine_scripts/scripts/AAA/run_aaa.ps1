param(
    [string]$ContextFolder = "",
    [int]$Limit = 30
)

$ErrorActionPreference = "Stop"
$scriptPath = $MyInvocation.MyCommand.Path
$aaaRoot = Split-Path -Parent $scriptPath
$engineScripts = Resolve-Path (Join-Path $aaaRoot "..")
$favoritesPath = Join-Path $aaaRoot "favorites.txt"

Write-Host "AAA Engine Menu" -ForegroundColor Cyan
if ($ContextFolder) {
    Write-Host ("Context: {0}" -f $ContextFolder) -ForegroundColor DarkGray
    $env:AAA_CONTEXT_FOLDER = $ContextFolder
}

$include = @('*.py','*.ps1','*.bat','*.cmd','*.sh')
$items = Get-ChildItem -Path $engineScripts -Recurse -File -Include $include |
    Where-Object {
        $_.FullName -notmatch '\\AAA\\' -and
        $_.FullName -notmatch '\\_migrated\\_logs\\' -and
        $_.Name -notmatch '^AAA_MENU\.bat$'
    }

if (-not $items) {
    Write-Host "No runnable scripts found." -ForegroundColor Yellow
    exit 0
}

$favorites = @()
if (Test-Path $favoritesPath) {
    $favorites = Get-Content -Path $favoritesPath | Where-Object { $_ -and -not $_.StartsWith('#') }
}

$scored = $items | ForEach-Object {
    $rel = $_.FullName.Substring($engineScripts.Path.Length + 1)
    $score = 1000
    foreach ($f in $favorites) {
        if ($rel -like "*$f*") { $score = 0; break }
    }
    [pscustomobject]@{
        Score = $score
        Name = $_.Name
        Ext = $_.Extension
        Full = $_.FullName
        Rel = $rel
    }
} | Sort-Object Score, Rel

$list = @($scored | Select-Object -First $Limit)

$idx = 1
$list | ForEach-Object {
    [pscustomobject]@{
        ID = $idx
        Name = $_.Name
        Type = $_.Ext
        Path = $_.Rel
    }
    $idx++
} | Format-Table -AutoSize

$choice = Read-Host "Pick action number (or q to quit)"
if ($choice -match '^[Qq]$') { exit 0 }
if (-not ($choice -match '^\d+$')) {
    Write-Host "Invalid selection." -ForegroundColor Red
    exit 1
}

$i = [int]$choice
if ($i -lt 1 -or $i -gt $list.Count) {
    Write-Host "Out of range." -ForegroundColor Red
    exit 1
}

$selected = $list[$i - 1]
$argsLine = Read-Host "Optional args (press Enter for none)"

Write-Host ("Running: {0}" -f $selected.Rel) -ForegroundColor Green

switch ($selected.Ext.ToLower()) {
    '.py'  { if ($argsLine) { & python $selected.Full $argsLine } else { & python $selected.Full } }
    '.ps1' { if ($argsLine) { & powershell -NoProfile -ExecutionPolicy Bypass -File $selected.Full $argsLine } else { & powershell -NoProfile -ExecutionPolicy Bypass -File $selected.Full } }
    '.bat' { if ($argsLine) { & $selected.Full $argsLine } else { & $selected.Full } }
    '.cmd' { if ($argsLine) { & $selected.Full $argsLine } else { & $selected.Full } }
    '.sh'  { if ($argsLine) { & bash $selected.Full $argsLine } else { & bash $selected.Full } }
    default { Write-Host "Unsupported script type." -ForegroundColor Yellow }
}
