# MORAL DECAY PROJECT - CLEANUP SCRIPT
# Run with: .\Cleanup-Structure.ps1 -WhatIf   (preview)
# Run with: .\Cleanup-Structure.ps1           (execute)

param(
    [switch]$WhatIf
)

$root = 'O:\_THEO\THEO\TM SUBSTACK\03_PUBLICATIONS\TRANS_DOMAIN_UNITY\The_Moral_Decay_of_America_Project'
$inner = Join-Path $root 'The_Moral_Decay_of_America_Project'

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "MORAL DECAY PROJECT CLEANUP" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

if ($WhatIf) {
    Write-Host "[PREVIEW MODE - No changes will be made]" -ForegroundColor Yellow
    Write-Host ""
}

# ============================================
# STEP 1: Create new folder structure
# ============================================
Write-Host "STEP 1: Creating folder structure..." -ForegroundColor Green

$newFolders = @(
    "_UNSORTED",
    "_TIER_1_FREE",
    "_TIER_2_UPGRADE",
    "_TIER_3_ACADEMIA",
    "06_Working_Notes",
    "06_Working_Notes\RAW_DATA_ARCHIVE",
    "07_Data_Core",
    "07_Data_Core\Evidence_Bundles",
    "07_Data_Core\Citation_Map",
    "08_Audio"
)

foreach ($folder in $newFolders) {
    $path = Join-Path $root $folder
    if (-not (Test-Path $path)) {
        if ($WhatIf) {
            Write-Host "  [WOULD CREATE] $folder" -ForegroundColor DarkGray
        } else {
            New-Item -Path $path -ItemType Directory -Force | Out-Null
            Write-Host "  [CREATED] $folder" -ForegroundColor Green
        }
    } else {
        Write-Host "  [EXISTS] $folder" -ForegroundColor Gray
    }
}

# ============================================
# STEP 2: Move unique files from inner folder
# ============================================
Write-Host ""
Write-Host "STEP 2: Moving unique files from nested folder..." -ForegroundColor Green

# Build hash of outer files
$outerFiles = Get-ChildItem $root -File -Recurse | Where-Object { $_.FullName -notlike '*\The_Moral_Decay_of_America_Project\The_Moral_Decay_of_America_Project\*' }
$outerHashes = @{}
foreach ($f in $outerFiles) {
    try {
        $hash = (Get-FileHash $f.FullName -Algorithm MD5 -ErrorAction Stop).Hash
        $outerHashes[$hash] = $f
    } catch { }
}

# Find and move unique inner files
$innerFiles = Get-ChildItem $inner -File -Recurse
$movedCount = 0
$skippedCount = 0

foreach ($f in $innerFiles) {
    $hash = $null
    try {
        $hash = (Get-FileHash $f.FullName -Algorithm MD5 -ErrorAction Stop).Hash
    } catch { }

    if ($hash -and $outerHashes.ContainsKey($hash)) {
        # Duplicate - skip
        $skippedCount++
        continue
    }

    # Unique file - determine destination
    $relativePath = $f.FullName.Replace($inner, '').TrimStart('\')

    # Map inner paths to outer structure
    $destPath = $relativePath
    if ($relativePath -like 'Story\*.wav' -or $relativePath -like '*.wav') {
        $destPath = "08_Audio\" + $f.Name
    } elseif ($relativePath -like '04_Data_Core\*') {
        $destPath = "07_Data_Core\" + $relativePath.Replace('04_Data_Core\', '')
    } elseif ($relativePath -like '06_Working_Notes\*') {
        $destPath = $relativePath  # Keep same structure
    } elseif ($relativePath -like 'Story\*') {
        # Story duplicates - check if audio
        if ($f.Extension -eq '.wav') {
            $destPath = "08_Audio\" + $f.Name
        } else {
            $destPath = "01_Stories\" + $f.Name
        }
    } elseif ($relativePath -like 'Notes\*') {
        $destPath = "06_Working_Notes\" + $f.Name
    }

    $fullDest = Join-Path $root $destPath
    $destDir = Split-Path $fullDest -Parent

    if ($WhatIf) {
        Write-Host "  [WOULD MOVE] $relativePath -> $destPath" -ForegroundColor DarkGray
    } else {
        if (-not (Test-Path $destDir)) {
            New-Item -Path $destDir -ItemType Directory -Force | Out-Null
        }
        if (-not (Test-Path $fullDest)) {
            Move-Item $f.FullName $fullDest -Force
            Write-Host "  [MOVED] $($f.Name)" -ForegroundColor Green
        } else {
            Write-Host "  [SKIP - EXISTS] $($f.Name)" -ForegroundColor Yellow
        }
    }
    $movedCount++
}

Write-Host "  Moved: $movedCount | Skipped duplicates: $skippedCount"

# ============================================
# STEP 3: Collect Untitled files to _UNSORTED
# ============================================
Write-Host ""
Write-Host "STEP 3: Moving Untitled files to _UNSORTED..." -ForegroundColor Green

$untitledFiles = Get-ChildItem $root -File -Recurse | Where-Object {
    $_.Name -like 'Untitled*' -and
    $_.FullName -notlike '*\_UNSORTED\*' -and
    $_.FullName -notlike '*\The_Moral_Decay_of_America_Project\The_Moral_Decay_of_America_Project\*'
}

$unsortedPath = Join-Path $root '_UNSORTED'
$untitledCount = 0

foreach ($f in $untitledFiles) {
    $sourcePath = Split-Path $f.FullName -Parent
    $sourceFolder = Split-Path $sourcePath -Leaf

    # Rename to include source folder
    $newName = "$sourceFolder`_$($f.Name)"
    if ($sourceFolder -eq 'The_Moral_Decay_of_America_Project') {
        $newName = "ROOT_$($f.Name)"
    }

    $dest = Join-Path $unsortedPath $newName

    if ($WhatIf) {
        Write-Host "  [WOULD MOVE] $($f.Name) from $sourceFolder" -ForegroundColor DarkGray
    } else {
        if (-not (Test-Path $dest)) {
            Move-Item $f.FullName $dest -Force
            Write-Host "  [MOVED] $($f.Name) -> $newName" -ForegroundColor Green
        } else {
            # Add number suffix if exists
            $base = [System.IO.Path]::GetFileNameWithoutExtension($newName)
            $ext = [System.IO.Path]::GetExtension($newName)
            $counter = 2
            while (Test-Path $dest) {
                $newName = "$base`_$counter$ext"
                $dest = Join-Path $unsortedPath $newName
                $counter++
            }
            Move-Item $f.FullName $dest -Force
            Write-Host "  [MOVED] $($f.Name) -> $newName" -ForegroundColor Green
        }
    }
    $untitledCount++
}

Write-Host "  Untitled files moved: $untitledCount"

# ============================================
# STEP 4: Delete empty inner folder
# ============================================
Write-Host ""
Write-Host "STEP 4: Cleaning up nested folder..." -ForegroundColor Green

if ($WhatIf) {
    Write-Host "  [WOULD DELETE] Nested The_Moral_Decay_of_America_Project folder" -ForegroundColor DarkGray
} else {
    # Check if inner has any remaining files
    $remainingFiles = Get-ChildItem $inner -File -Recurse
    if ($remainingFiles.Count -eq 0) {
        Remove-Item $inner -Recurse -Force
        Write-Host "  [DELETED] Nested folder (was empty)" -ForegroundColor Green
    } else {
        Write-Host "  [KEPT] Nested folder has $($remainingFiles.Count) remaining files" -ForegroundColor Yellow
        foreach ($f in $remainingFiles | Select-Object -First 10) {
            Write-Host "    - $($f.FullName.Replace($inner, ''))" -ForegroundColor Gray
        }
    }
}

# ============================================
# SUMMARY
# ============================================
Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "CLEANUP COMPLETE" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan

if ($WhatIf) {
    Write-Host ""
    Write-Host "This was a preview. Run without -WhatIf to execute." -ForegroundColor Yellow
}
