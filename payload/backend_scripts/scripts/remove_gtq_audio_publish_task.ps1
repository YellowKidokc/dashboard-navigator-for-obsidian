param(
    [string]$TaskName = "FORGE_GTQ_Audio_AutoPublish"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$existing = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if (-not $existing) {
    Write-Host "[GTQ] Task '$TaskName' not found."
    exit 0
}

Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
Write-Host "[GTQ] Removed task '$TaskName'."
