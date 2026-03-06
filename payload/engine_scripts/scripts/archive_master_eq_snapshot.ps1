param(
    [string]$VaultRoot = "O:\_Theophysics_v3",
    [Parameter(Mandatory = $true)]
    [string]$SourceFolderName,
    [string]$ArchiveRoot = "T:\ARCHIVE\_Theophysics_v3\MASTER_EQ_CONSOLIDATED"
)

$ErrorActionPreference = "Stop"

function Count-MarkdownFiles([string]$Path) {
    if (-not (Test-Path $Path)) { return 0 }
    return (Get-ChildItem -Path $Path -Recurse -File -Filter *.md -ErrorAction SilentlyContinue | Measure-Object).Count
}

function Count-AllFiles([string]$Path) {
    if (-not (Test-Path $Path)) { return 0 }
    return (Get-ChildItem -Path $Path -Recurse -File -ErrorAction SilentlyContinue | Measure-Object).Count
}

function Sum-Bytes([string]$Path) {
    if (-not (Test-Path $Path)) { return 0 }
    return (Get-ChildItem -Path $Path -Recurse -File -ErrorAction SilentlyContinue | Measure-Object Length -Sum).Sum
}

$masterEqRoot = Join-Path $VaultRoot "MASTER_EQ_CONSOLIDATED"
$source = Join-Path $masterEqRoot $SourceFolderName
$destination = Join-Path $ArchiveRoot $SourceFolderName
$outputDir = Join-Path $VaultRoot "00_SYSTEM\01_ENGINE\scripts\output"

if (-not (Test-Path $source)) {
    throw "Source folder not found: $source"
}
if (Test-Path $destination) {
    throw "Destination already exists: $destination"
}

New-Item -ItemType Directory -Force -Path $ArchiveRoot | Out-Null
New-Item -ItemType Directory -Force -Path $outputDir | Out-Null

$ts = Get-Date -Format "yyyyMMdd_HHmmss"
$logPath = Join-Path $outputDir "archive_master_eq_$($SourceFolderName)_$ts.log"
$receiptPath = Join-Path $outputDir "archive_master_eq_$($SourceFolderName)_$ts.md"

$sourceMdBefore = Count-MarkdownFiles $source
$sourceFilesBefore = Count-AllFiles $source
$sourceBytesBefore = Sum-Bytes $source

Write-Host "Archiving: $source" -ForegroundColor Cyan
Write-Host "To:        $destination" -ForegroundColor Cyan

robocopy $source $destination /E /MOVE /R:1 /W:1 /NFL /NDL /NP /NJH /NJS /LOG:$logPath | Out-Null
$rc = $LASTEXITCODE
if ($rc -ge 8) {
    throw "Robocopy failed with exit code $rc. Log: $logPath"
}

$sourceExistsAfter = Test-Path $source
$destMdAfter = Count-MarkdownFiles $destination
$destFilesAfter = Count-AllFiles $destination
$destBytesAfter = Sum-Bytes $destination
$destGbAfter = [math]::Round(($destBytesAfter / 1GB), 3)

$receipt = @"
# Master EQ Archive Receipt

- Timestamp: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")
- Source folder name: $SourceFolderName
- Source path: $source
- Destination path: $destination
- Robocopy exit code: $rc
- Log path: $logPath

## Pre-Move Source Counts
- Markdown files: $sourceMdBefore
- Total files: $sourceFilesBefore
- Total bytes: $sourceBytesBefore

## Post-Move Verification
- Source exists after move: $sourceExistsAfter
- Destination markdown files: $destMdAfter
- Destination total files: $destFilesAfter
- Destination total bytes: $destBytesAfter
- Destination size GB: $destGbAfter
"@

Set-Content -Path $receiptPath -Value $receipt -Encoding UTF8

Write-Host "Archive complete." -ForegroundColor Green
Write-Host "Receipt: $receiptPath"
Write-Host "Log:     $logPath"
