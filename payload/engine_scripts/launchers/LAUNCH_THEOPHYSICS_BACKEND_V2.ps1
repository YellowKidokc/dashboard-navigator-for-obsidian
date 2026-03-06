$ErrorActionPreference = "Stop"

$backendRoot = if ($env:THEOPHYSICS_BACKEND_ROOT) { $env:THEOPHYSICS_BACKEND_ROOT } else { "O:\999_IGNORE\Obsidian Programs\Python_Backend" }
$pythonExe = Join-Path $backendRoot "venv\Scripts\python.exe"
$appFile = Join-Path $backendRoot "app_v2.py"

if (-not (Test-Path $backendRoot)) {
    Write-Error "Backend folder not found: $backendRoot"
}

if (-not (Test-Path $pythonExe)) {
    Write-Error "Python executable not found: $pythonExe"
}

if (-not (Test-Path $appFile)) {
    Write-Error "App file not found: $appFile"
}

$proc = Start-Process -FilePath $pythonExe -ArgumentList "app_v2.py" -WorkingDirectory $backendRoot -PassThru
Write-Host "Launched Theophysics Backend V2 (PID: $($proc.Id))"
