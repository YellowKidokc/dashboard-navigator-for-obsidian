param(
    [Parameter(Mandatory = $true)]
    [string]$RepoPath,

    [string]$EngineRoot = "O:\_Theophysics_v3\00_SYSTEM\00_ENGINE\01_ENGINE",
    [string]$BackendRoot = "O:\999_IGNORE\Obsidian Programs\Python_Backend",
    [string]$PayloadRoot = "payload",
    [switch]$IncludeMarkdown
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Ensure-Dir {
    param([string]$Path)
    if (-not (Test-Path -LiteralPath $Path)) {
        New-Item -Path $Path -ItemType Directory -Force | Out-Null
    }
}

function Get-ScriptFiles {
    param(
        [string]$Root,
        [string[]]$Extensions,
        [string[]]$SkipDirs
    )

    if (-not (Test-Path -LiteralPath $Root)) {
        throw "Source root not found: $Root"
    }

    $files = Get-ChildItem -LiteralPath $Root -Recurse -File -ErrorAction SilentlyContinue
    $secretPatterns = @(
        'ghp_[A-Za-z0-9]{36}',
        'github_pat_[A-Za-z0-9_]{20,}',
        'sk-[A-Za-z0-9]{20,}',
        'AIza[0-9A-Za-z\-_]{20,}'
    )

    $selected = foreach ($f in $files) {
        $skip = $false
        foreach ($d in $SkipDirs) {
            if ($f.FullName -match [regex]::Escape("\$d\")) {
                $skip = $true
                break
            }
        }
        if ($skip) { continue }

        if ($Extensions -contains $f.Extension.ToLowerInvariant()) {
            try {
                $content = Get-Content -LiteralPath $f.FullName -Raw -ErrorAction Stop
                foreach ($p in $secretPatterns) {
                    if ($content -match $p) {
                        $skip = $true
                        break
                    }
                }
            } catch {
                # If unreadable, keep file unless directory filter excluded it.
            }
            if ($skip) { continue }
            $f
        }
    }
    return $selected
}

function Copy-WithStructure {
    param(
        [System.IO.FileInfo[]]$Files,
        [string]$SourceRoot,
        [string]$DestRoot
    )

    foreach ($f in $Files) {
        $relative = $f.FullName.Substring($SourceRoot.Length).TrimStart('\')
        $target = Join-Path $DestRoot $relative
        Ensure-Dir -Path (Split-Path -Parent $target)
        Copy-Item -LiteralPath $f.FullName -Destination $target -Force
    }
}

$repoFull = (Resolve-Path -LiteralPath $RepoPath).Path
if (-not (Test-Path -LiteralPath (Join-Path $repoFull ".git"))) {
    throw "RepoPath is not a git repo: $repoFull"
}

$exts = @(".ps1", ".bat", ".cmd", ".py", ".ahk", ".sh", ".js", ".ts")
if ($IncludeMarkdown) {
    $exts += @(".md", ".json", ".yaml", ".yml")
}

$skipDirs = @(
    ".git", "node_modules", "venv", "venv_backup", "__pycache__", "dist", "build",
    ".obsidian\plugins", "tmp", "cache", ".trash", ".archive", ".idea", ".vscode",
    "MCP_Setup"
)

$payloadBase = Join-Path $repoFull $PayloadRoot
$engineDst = Join-Path $payloadBase "engine_scripts"
$backendDst = Join-Path $payloadBase "backend_scripts"
Ensure-Dir -Path $payloadBase
Ensure-Dir -Path $engineDst
Ensure-Dir -Path $backendDst

Write-Host "[1/4] Scanning engine scripts..."
$engineFiles = Get-ScriptFiles -Root $EngineRoot -Extensions $exts -SkipDirs $skipDirs
Write-Host "[2/4] Scanning backend scripts..."
$backendFiles = Get-ScriptFiles -Root $BackendRoot -Extensions $exts -SkipDirs $skipDirs

Write-Host "[3/4] Copying files with folder structure..."
Copy-WithStructure -Files $engineFiles -SourceRoot $EngineRoot -DestRoot $engineDst
Copy-WithStructure -Files $backendFiles -SourceRoot $BackendRoot -DestRoot $backendDst

Write-Host "[4/4] Writing inventory..."
$inventoryPath = Join-Path $payloadBase "script_inventory.csv"
$rows = @()

foreach ($f in $engineFiles) {
    $rows += [PSCustomObject]@{
        source_group = "engine"
        source_root  = $EngineRoot
        source_path  = $f.FullName
        extension    = $f.Extension
        size_bytes   = $f.Length
        modified     = $f.LastWriteTime.ToString("s")
    }
}
foreach ($f in $backendFiles) {
    $rows += [PSCustomObject]@{
        source_group = "backend"
        source_root  = $BackendRoot
        source_path  = $f.FullName
        extension    = $f.Extension
        size_bytes   = $f.Length
        modified     = $f.LastWriteTime.ToString("s")
    }
}

$rows | Sort-Object source_group, source_path | Export-Csv -Path $inventoryPath -NoTypeInformation -Encoding UTF8

Write-Host ""
Write-Host "Done."
Write-Host "Repo:        $repoFull"
Write-Host "Payload:     $payloadBase"
Write-Host "Engine files: $($engineFiles.Count)"
Write-Host "Backend files: $($backendFiles.Count)"
Write-Host "Inventory:   $inventoryPath"
Write-Host ""
Write-Host "Next:"
Write-Host "  git -C `"$repoFull`" add $PayloadRoot"
Write-Host "  git -C `"$repoFull`" commit -m `"chore: stage dashboard++ engine/backend payload`""
Write-Host "  git -C `"$repoFull`" push"
