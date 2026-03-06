# Generate full inventory for release planning
$root = 'O:\_THEO\THEO\TM SUBSTACK\03_PUBLICATIONS\TRANS_DOMAIN_UNITY\The_Moral_Decay_of_America_Project'

$results = @()
$seq = 1

# Get all markdown/content files (exclude scripts, temp files)
$files = Get-ChildItem $root -File -Recurse | Where-Object {
    $_.Extension -in @('.md', '.pdf', '.html') -and
    $_.FullName -notlike '*\_UNSORTED\*' -and
    $_.FullName -notlike '*\08_Audio\*' -and
    $_.Name -notlike '*.ps1'
}

foreach ($f in $files | Sort-Object FullName) {
    $rel = $f.FullName.Replace($root + '\', '')
    $folder = Split-Path $rel -Parent
    if (-not $folder) { $folder = 'ROOT' }
    
    # Auto-assign tier based on content type
    $tier = 'TBD'
    if ($rel -like '01_Stories\*') { $tier = 'FREE' }
    elseif ($rel -like '02_Theoretical_Framework\P 0*') { $tier = 'UPGRADE' }
    elseif ($rel -like '*Domain_Analysis\*') { $tier = 'ACADEMIA' }
    elseif ($rel -like '*Decade_Reports\*') { $tier = 'UPGRADE' }
    elseif ($rel -like '*Decade_Analysis_Overviews\*') { $tier = 'FREE' }
    elseif ($rel -like '*Control_Group_Amish\*') { $tier = 'UPGRADE' }
    elseif ($rel -like '*Case_Studies\*') { $tier = 'UPGRADE' }
    elseif ($rel -like '*Social_Physics_Essays\*') { $tier = 'ACADEMIA' }
    elseif ($rel -like '00_CANONICAL_THEOPHYSICS_SYNTHESIS\*') { $tier = 'ACADEMIA' }
    elseif ($rel -like 'Moral_Decline_Series_Substack\*') { $tier = 'FREE' }
    elseif ($rel -like '*LAYER_*') { $tier = 'ACADEMIA' }
    elseif ($rel -like '06_Working_Notes\*') { $tier = 'SKIP' }
    elseif ($rel -like '07_Data_Core\*') { $tier = 'SKIP' }
    
    # Get word count
    $words = 0
    if ($f.Extension -eq '.md') {
        try {
            $content = Get-Content $f.FullName -Raw -ErrorAction Stop
            $words = ($content -split '\s+').Count
        } catch { }
    }
    
    $results += [PSCustomObject]@{
        Seq = $seq
        Tier = $tier
        Folder = $folder
        FileName = $f.Name
        Words = $words
        RelPath = $rel
        ReleaseWeek = ''
        Notes = ''
    }
    $seq++
}

# Export to CSV
$csvPath = Join-Path $root 'RELEASE_INVENTORY.csv'
$results | Export-Csv $csvPath -NoTypeInformation -Encoding UTF8

# Summary
Write-Host "=== INVENTORY COMPLETE ===" -ForegroundColor Cyan
Write-Host "Total files: $($results.Count)"
Write-Host ""
Write-Host "BY TIER:" -ForegroundColor Yellow
$results | Group-Object Tier | ForEach-Object {
    Write-Host "  $($_.Name): $($_.Count) files"
}
Write-Host ""
Write-Host "BY FOLDER:" -ForegroundColor Yellow
$results | Group-Object Folder | Sort-Object Count -Descending | Select-Object -First 15 | ForEach-Object {
    Write-Host "  $($_.Name): $($_.Count)"
}
Write-Host ""
Write-Host "Saved to: $csvPath" -ForegroundColor Green
