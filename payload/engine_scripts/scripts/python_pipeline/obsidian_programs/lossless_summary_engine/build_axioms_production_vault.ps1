param(
    [string]$DocsRoot = "",
    [string[]]$ScanDrives = @("C","D","O","T"),
    [string]$TProductionAxiomsPath = "T:\Theophysics production\01_AXIOMS",
    [string[]]$FocusedRoots = @(),
    [switch]$IncludeSequenceCoded,
    [int]$MaxFileMB = 25
)

$ErrorActionPreference = "Stop"

function Get-NowStamp {
    return (Get-Date -Format "yyyyMMdd_HHmmss")
}

function Get-DocsRoot {
    param([string]$Override)
    if (-not [string]::IsNullOrWhiteSpace($Override)) { return $Override }
    return [Environment]::GetFolderPath("MyDocuments")
}

function Get-CategoryFromToken {
    param(
        [string]$Token,
        [string]$PathLower
    )

    $prefix = ""
    if (-not [string]::IsNullOrWhiteSpace($Token)) {
        $m = [regex]::Match($Token, "^([A-Z]+)")
        if ($m.Success) { $prefix = $m.Groups[1].Value.ToUpperInvariant() }
    }

    switch ($prefix) {
        "A" { return "Axioms" }
        "D" { return "Definitions" }
        "E" { return "Equations" }
        "P" { return "Propositions" }
        "T" { return "Theorems" }
        "LN" { return "Laws_And_Lemmas" }
        "BC" { return "Boundary_Conditions" }
        "ID" { return "Identifications" }
        "C" { return "Corollaries" }
        "U" { return "Universals" }
        "F" { return "Fruits_And_Domains" }
        "PROT" { return "Protocols" }
        "PRED" { return "Predictions" }
        "FALS" { return "Falsification" }
        "OPEN" { return "Open_Questions" }
        "EV" { return "Evidence" }
        "SC" { return "Scale_Coherence" }
        "META" { return "Meta_System" }
        "FINAL" { return "Final_Results" }
        "BRIDGE" { return "Bridge_Claims" }
        "O" { return "Ontology" }
    }

    if ($PathLower -match "equation|master_eq|master-eq") { return "Equations" }
    if ($PathLower -match "theorem") { return "Theorems" }
    if ($PathLower -match "definition") { return "Definitions" }
    if ($PathLower -match "axiom") { return "Axioms" }
    if ($PathLower -match "canon") { return "Canonical" }
    if ($PathLower -match "proof|lemma|law") { return "Laws_And_Lemmas" }
    if ($PathLower -match "evidence|validation") { return "Evidence" }
    return "Misc"
}

function New-SafeName {
    param([string]$Name)
    $out = $Name -replace "[^\w\.\- ]","_"
    $out = $out -replace "\s+","-"
    return $out
}

function Add-FileCandidates {
    param(
        [System.Collections.Generic.List[object]]$Collector,
        [System.IO.FileInfo[]]$Files,
        [string]$Reason,
        [long]$MaxBytes
    )
    foreach ($f in $Files) {
        if ($f.Length -gt $MaxBytes) { continue }
        $Collector.Add([pscustomobject]@{
            FullName = $f.FullName
            Name = $f.Name
            Extension = $f.Extension.ToLowerInvariant()
            Reason = $Reason
        }) | Out-Null
    }
}

$ts = Get-NowStamp
$docs = Get-DocsRoot -Override $DocsRoot
$destRoot = Join-Path $docs ("Axioms_Production_Vault_" + $ts)
$canonicalDir = Join-Path $destRoot "00_CANONICAL_SEQUENTIAL"
$categoryRoot = Join-Path $destRoot "01_CATEGORIES"
$rawDir = Join-Path $destRoot "02_RAW_UNIQUE"
$metaDir = Join-Path $destRoot "99_META"

New-Item -ItemType Directory -Path $destRoot,$canonicalDir,$categoryRoot,$rawDir,$metaDir -Force | Out-Null

$candidateExt = @(".md",".txt",".docx",".pdf",".json",".csv",".xlsx")
$excludeRegex = "(\\|/)(\.git|node_modules|venv|__pycache__|\.obsidian|_LOSSLESS_SUMMARY_)(\\|/)"
$candidates = New-Object System.Collections.Generic.List[object]
$maxBytes = [long]$MaxFileMB * 1MB

if ($FocusedRoots.Count -gt 0) {
    Write-Output "Scanning explicit focused roots for '*axiom*' files..."
    foreach ($seed in ($FocusedRoots | Sort-Object -Unique)) {
        if (-not (Test-Path $seed)) { continue }
        try {
            $found = Get-ChildItem -Path $seed -Recurse -File -Filter "*axiom*" -ErrorAction SilentlyContinue
            $filtered = $found | Where-Object {
                ($candidateExt -contains $_.Extension.ToLowerInvariant()) -and
                ($_.FullName -notmatch $excludeRegex)
            }
            Add-FileCandidates -Collector $candidates -Files $filtered -Reason ("name_or_path_axiom@focused") -MaxBytes $maxBytes
        } catch {}
    }
} else {
    Write-Output "Scanning focused drive roots for '*axiom*' files..."
    foreach ($d in $ScanDrives) {
        $root = "$d`:\"
        if (-not (Test-Path $root)) { continue }
        try {
            $seedDirs = @()
            $top = Get-ChildItem -Path $root -Directory -ErrorAction SilentlyContinue
            foreach ($td in $top) {
                if ($td.Name -match "(?i)theophysics|axiom|obsidian|vault|canon|documents") {
                    $seedDirs += $td.FullName
                }
            }
            if ($d -eq "C") {
                $userDocs = Get-DocsRoot -Override $DocsRoot
                if (Test-Path $userDocs) { $seedDirs += $userDocs }
            }
            if ($seedDirs.Count -eq 0) { continue }

            foreach ($seed in ($seedDirs | Sort-Object -Unique)) {
                $found = Get-ChildItem -Path $seed -Recurse -File -Filter "*axiom*" -ErrorAction SilentlyContinue
                $filtered = $found | Where-Object {
                    ($candidateExt -contains $_.Extension.ToLowerInvariant()) -and
                    ($_.FullName -notmatch $excludeRegex)
                }
                Add-FileCandidates -Collector $candidates -Files $filtered -Reason ("name_or_path_axiom@" + $d) -MaxBytes $maxBytes
            }
        } catch {}
    }
}

Write-Output "Adding canonical T: axioms..."
if (Test-Path $TProductionAxiomsPath) {
    $canonFiles = Get-ChildItem -Path $TProductionAxiomsPath -Recurse -File -ErrorAction SilentlyContinue | Where-Object {
        ($candidateExt -contains $_.Extension.ToLowerInvariant()) -and
        ($_.FullName -notmatch $excludeRegex)
    }
    Add-FileCandidates -Collector $candidates -Files $canonFiles -Reason "canonical_t_axioms" -MaxBytes $maxBytes
}

if ($IncludeSequenceCoded) {
    Write-Output "Adding sequence-coded Theophysics files..."
    $knownRoots = @(
        "O:\_Theophysics_v3",
        "T:\Theophysics production",
        (Join-Path (Get-DocsRoot -Override $DocsRoot) "A flat\_Theophysics"),
        (Join-Path (Get-DocsRoot -Override $DocsRoot) "02_THEOPHYSICS")
    )
    foreach ($kr in $knownRoots) {
        if (-not (Test-Path $kr)) { continue }
        try {
            $seqFiles = Get-ChildItem -Path $kr -Recurse -File -Include *.md,*.txt -ErrorAction SilentlyContinue | Where-Object {
                $_.Name -match "^\d{3}_[A-Z]" -and $_.FullName -notmatch $excludeRegex
            }
            Add-FileCandidates -Collector $candidates -Files $seqFiles -Reason "sequence_coded" -MaxBytes $maxBytes
        } catch {}
    }
}

$candidates = $candidates | Sort-Object FullName -Unique
Write-Output ("Candidate files: " + $candidates.Count)

$records = New-Object System.Collections.Generic.List[object]
$hashToPrimary = @{}
$seqRows = New-Object System.Collections.Generic.List[object]
$catCounts = @{}

$idx = 0
foreach ($c in $candidates) {
    $idx++
    if (-not (Test-Path $c.FullName)) { continue }

    $hash = (Get-FileHash -Path $c.FullName -Algorithm SHA256).Hash
    $isDuplicate = $hashToPrimary.ContainsKey($hash)
    $duplicateOf = ""
    if ($isDuplicate) { $duplicateOf = $hashToPrimary[$hash] }
    else { $hashToPrimary[$hash] = $c.FullName }

    $baseNoExt = [System.IO.Path]::GetFileNameWithoutExtension($c.Name)
    $seq = $null
    $token = ""
    $m = [regex]::Match($baseNoExt, "^(\d{3})_([^_]+)")
    if ($m.Success) {
        $seq = [int]$m.Groups[1].Value
        $token = $m.Groups[2].Value
    }

    $category = Get-CategoryFromToken -Token $token -PathLower $c.FullName.ToLowerInvariant()
    if (-not $catCounts.ContainsKey($category)) { $catCounts[$category] = 0 }
    $catCounts[$category] += 1

    $hashShort = $hash.Substring(0,8)
    $safeName = New-SafeName -Name $c.Name
    $rawName = $hashShort + "__" + $safeName
    $rawPath = Join-Path $rawDir $rawName

    if (-not $isDuplicate) {
        Copy-Item -Path $c.FullName -Destination $rawPath -Force

        $catDir = Join-Path $categoryRoot $category
        New-Item -ItemType Directory -Path $catDir -Force | Out-Null
        $catName = "{0}__{1}" -f $hashShort, $safeName
        Copy-Item -Path $c.FullName -Destination (Join-Path $catDir $catName) -Force

        if ($null -ne $seq) {
            $canonName = "{0:D3}__{1}" -f $seq, $safeName
            $canonPath = Join-Path $canonicalDir $canonName
            if (-not (Test-Path $canonPath)) {
                Copy-Item -Path $c.FullName -Destination $canonPath -Force
            } else {
                $altName = "{0:D3}__{1}__{2}" -f $seq, $hashShort, $safeName
                Copy-Item -Path $c.FullName -Destination (Join-Path $canonicalDir $altName) -Force
            }
            $seqRows.Add([pscustomobject]@{
                seq = $seq
                token = $token
                name = $c.Name
                source = $c.FullName
            }) | Out-Null
        }
    }

    $records.Add([pscustomobject]@{
        source_path = $c.FullName
        reason = $c.Reason
        sha256 = $hash
        duplicate = $isDuplicate
        duplicate_of = $duplicateOf
        seq = $seq
        token = $token
        category = $category
    }) | Out-Null
}

$mapCsv = Join-Path $metaDir ("AXIOM_SOURCE_MAP_" + $ts + ".csv")
$records | Export-Csv -Path $mapCsv -NoTypeInformation -Encoding UTF8

$seqIndex = Join-Path $metaDir "00_INDEX_CANONICAL_SEQUENTIAL.md"
$seqLines = @()
$seqLines += "# Canonical Sequential Index"
$seqLines += ""
$seqLines += ("Generated: " + $ts)
$seqLines += ""
$orderedSeq = $seqRows | Sort-Object seq, name
foreach ($r in $orderedSeq) {
    $seqLines += ("- {0:D3} | {1} | {2}" -f $r.seq, $r.token, $r.name)
}
Set-Content -Path $seqIndex -Value $seqLines -Encoding UTF8

$catIndex = Join-Path $metaDir "00_INDEX_CATEGORIES.md"
$catLines = @()
$catLines += "# Category Index"
$catLines += ""
$catLines += ("Generated: " + $ts)
$catLines += ""
foreach ($k in ($catCounts.Keys | Sort-Object)) {
    $catLines += ("- " + $k + ": " + $catCounts[$k])
}
Set-Content -Path $catIndex -Value $catLines -Encoding UTF8

$summary = Join-Path $metaDir "BUILD_SUMMARY.md"
$uniqueCount = ($records | Where-Object { -not $_.duplicate }).Count
$dupCount = ($records | Where-Object { $_.duplicate }).Count
$sumLines = @()
$sumLines += "# Build Summary"
$sumLines += ""
$sumLines += ("Generated: " + $ts)
$sumLines += ("Destination: " + $destRoot)
$sumLines += ("Candidate files: " + $records.Count)
$sumLines += ("Unique files copied: " + $uniqueCount)
$sumLines += ("Duplicates skipped by hash: " + $dupCount)
Set-Content -Path $summary -Value $sumLines -Encoding UTF8

$zipPath = Join-Path $docs ("Axioms_Production_Vault_" + $ts + ".zip")
Compress-Archive -Path $destRoot -DestinationPath $zipPath -CompressionLevel Optimal -Force

$tZip = $null
$tFolder = $null
if (Test-Path $TProductionAxiomsPath) {
    $tZip = Join-Path $TProductionAxiomsPath ([System.IO.Path]::GetFileName($zipPath))
    Copy-Item -Path $zipPath -Destination $tZip -Force

    $tFolder = Join-Path $TProductionAxiomsPath ([System.IO.Path]::GetFileName($destRoot))
    if (Test-Path $tFolder) { Remove-Item -Path $tFolder -Recurse -Force }
    Copy-Item -Path $destRoot -Destination $tFolder -Recurse -Force
}

Write-Output ("DEST_ROOT=" + $destRoot)
Write-Output ("ZIP_PATH=" + $zipPath)
if ($null -ne $tZip) { Write-Output ("T_ZIP_PATH=" + $tZip) }
if ($null -ne $tFolder) { Write-Output ("T_FOLDER_PATH=" + $tFolder) }
Write-Output ("UNIQUE_FILES=" + $uniqueCount)
Write-Output ("DUPLICATES=" + $dupCount)
