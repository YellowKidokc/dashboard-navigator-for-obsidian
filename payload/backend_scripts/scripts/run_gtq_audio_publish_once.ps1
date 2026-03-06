param(
    [switch]$NoUploadDrive,
    [switch]$MoveFiles,
    [string]$AxiomsUrl = "[[00_Canonical/CANONICAL_INDEX|Canonical Axiom Index]]"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$pythonScript = Join-Path $PSScriptRoot "auto_audio_publish_gtq.py"
if (-not (Test-Path $pythonScript)) {
    throw "Missing script: $pythonScript"
}

$args = @("-3", $pythonScript, "--axioms-url", $AxiomsUrl)
if (-not $NoUploadDrive) { $args += "--upload-drive" }
if ($MoveFiles) { $args += "--move" }

Write-Host "[GTQ] Running audio publish pass..."
& py @args
$exitCode = $LASTEXITCODE
if ($exitCode -ne 0) {
    throw "auto_audio_publish_gtq.py failed with exit code $exitCode"
}

Write-Host "[GTQ] Pass complete."
