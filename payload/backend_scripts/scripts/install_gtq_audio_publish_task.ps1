param(
    [string]$TaskName = "FORGE_GTQ_Audio_AutoPublish",
    [int]$IntervalMinutes = 15,
    [switch]$NoUploadDrive,
    [switch]$MoveFiles
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if ($IntervalMinutes -lt 5) {
    throw "IntervalMinutes must be >= 5."
}

$runner = Join-Path $PSScriptRoot "run_gtq_audio_publish_once.ps1"
if (-not (Test-Path $runner)) {
    throw "Missing runner: $runner"
}

$taskCommand = 'powershell.exe -NoProfile -ExecutionPolicy Bypass -File \"' + $runner + '\"'
if ($NoUploadDrive) { $taskCommand += " -NoUploadDrive" }
if ($MoveFiles) { $taskCommand += " -MoveFiles" }

schtasks /Create /F /TN $TaskName /SC MINUTE /MO $IntervalMinutes /TR "$taskCommand" | Out-Null
if ($LASTEXITCODE -ne 0) {
    throw "Failed to create scheduled task '$TaskName'."
}

Write-Host "[GTQ] Installed task '$TaskName' every $IntervalMinutes minutes."
Write-Host "[GTQ] Runner: $runner"
