# Check for duplicates between outer and inner folders
$outer = 'O:\_THEO\THEO\TM SUBSTACK\03_PUBLICATIONS\TRANS_DOMAIN_UNITY\The_Moral_Decay_of_America_Project'
$inner = Join-Path $outer 'The_Moral_Decay_of_America_Project'

Write-Host "=== DUPLICATE CHECK ===" -ForegroundColor Cyan
Write-Host "Outer: $outer"
Write-Host "Inner: $inner"
Write-Host ""

# Get all files
$outerFiles = Get-ChildItem $outer -File -Recurse -ErrorAction SilentlyContinue | Where-Object { $_.FullName -notlike '*\The_Moral_Decay_of_America_Project\The_Moral_Decay_of_America_Project\*' }
$innerFiles = Get-ChildItem $inner -File -Recurse -ErrorAction SilentlyContinue

Write-Host "Outer files (excluding nested): $($outerFiles.Count)"
Write-Host "Inner files: $($innerFiles.Count)"
Write-Host ""

# Build hash tables
$outerHashes = @{}
$innerHashes = @{}

Write-Host "Hashing outer files..." -ForegroundColor Gray
foreach ($f in $outerFiles) {
    try {
        $hash = (Get-FileHash $f.FullName -Algorithm MD5 -ErrorAction Stop).Hash
        $outerHashes[$hash] = $f
    } catch { }
}

Write-Host "Hashing inner files..." -ForegroundColor Gray
foreach ($f in $innerFiles) {
    try {
        $hash = (Get-FileHash $f.FullName -Algorithm MD5 -ErrorAction Stop).Hash
        $innerHashes[$hash] = $f
    } catch { }
}

# Find duplicates and unique files
$duplicates = @()
$uniqueInner = @()

foreach ($hash in $innerHashes.Keys) {
    if ($outerHashes.ContainsKey($hash)) {
        $duplicates += [PSCustomObject]@{
            Hash = $hash
            InnerFile = $innerHashes[$hash].FullName
            OuterFile = $outerHashes[$hash].FullName
            Size = $innerHashes[$hash].Length
        }
    } else {
        $uniqueInner += $innerHashes[$hash]
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Yellow
Write-Host "EXACT DUPLICATES: $($duplicates.Count)" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Yellow
foreach ($d in $duplicates) {
    Write-Host "  DUPE: $($d.InnerFile.Replace($inner, '[INNER]'))"
    Write-Host "   ==>  $($d.OuterFile.Replace($outer, '[OUTER]'))"
    Write-Host ""
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "UNIQUE TO INNER (need to preserve): $($uniqueInner.Count)" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
foreach ($f in $uniqueInner) {
    $rel = $f.FullName.Replace($inner, '')
    Write-Host "  $rel"
}

# Summary
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "SUMMARY" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Duplicates to DELETE from inner: $($duplicates.Count)"
Write-Host "Unique files to MOVE from inner: $($uniqueInner.Count)"
Write-Host ""
Write-Host "After cleanup, inner folder can be removed."
