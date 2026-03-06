param(
    [string]$DocsRoot = "",
    [string]$TProductionAxiomsPath = "T:\Theophysics production\01_AXIOMS",
    [string[]]$SourceRoots = @(
        "O:\_Theophysics_v3\00_AXIOMS",
        "C:\Users\lowes\OneDrive\Documents\AXIOM",
        "C:\Users\lowes\OneDrive\Documents\THE Axioms Vault"
    )
)

$ErrorActionPreference = "Stop"

function Get-CategoryFromToken {
    param([string]$Token,[string]$PathLower)
    $m = [regex]::Match($Token, "^([A-Z]+)")
    $p = ""
    if ($m.Success) { $p = $m.Groups[1].Value.ToUpperInvariant() }
    switch ($p) {
        "A" { "Axioms"; break }
        "D" { "Definitions"; break }
        "E" { "Equations"; break }
        "P" { "Propositions"; break }
        "T" { "Theorems"; break }
        "LN" { "Laws_And_Lemmas"; break }
        "BC" { "Boundary_Conditions"; break }
        "ID" { "Identifications"; break }
        "C" { "Corollaries"; break }
        "U" { "Universals"; break }
        "F" { "Fruits_And_Domains"; break }
        "PROT" { "Protocols"; break }
        "PRED" { "Predictions"; break }
        "FALS" { "Falsification"; break }
        "OPEN" { "Open_Questions"; break }
        "EV" { "Evidence"; break }
        "SC" { "Scale_Coherence"; break }
        "META" { "Meta_System"; break }
        "FINAL" { "Final_Results"; break }
        "BRIDGE" { "Bridge_Claims"; break }
        default {
            if ($PathLower -match "equation|master_eq|master-eq") { "Equations" }
            elseif ($PathLower -match "theorem") { "Theorems" }
            elseif ($PathLower -match "definition") { "Definitions" }
            elseif ($PathLower -match "axiom") { "Axioms" }
            else { "Misc" }
        }
    }
}

$docs = if ([string]::IsNullOrWhiteSpace($DocsRoot)) { [Environment]::GetFolderPath("MyDocuments") } else { $DocsRoot }
$ts = Get-Date -Format "yyyyMMdd_HHmmss"
$dest = Join-Path $docs ("Axioms_Production_Vault_{0}" -f $ts)
$canonDir = Join-Path $dest "00_CANONICAL_SEQUENTIAL"
$catRoot = Join-Path $dest "01_CATEGORIES"
$rawDir = Join-Path $dest "02_RAW_UNIQUE"
$metaDir = Join-Path $dest "99_META"
New-Item -ItemType Directory -Path $dest,$canonDir,$catRoot,$rawDir,$metaDir -Force | Out-Null

$exts = @(".md",".txt",".docx",".pdf",".json",".csv",".xlsx")
$exclude = "(\\|/)(\.git|node_modules|venv|__pycache__|\.obsidian|_LOSSLESS_SUMMARY_)(\\|/)"
$candidates = New-Object System.Collections.Generic.List[object]

$canonical = $TProductionAxiomsPath
if (Test-Path $canonical) {
    Get-ChildItem -Path $canonical -Recurse -File -ErrorAction SilentlyContinue |
        Where-Object { $exts -contains $_.Extension.ToLowerInvariant() } |
        ForEach-Object {
            $candidates.Add([pscustomobject]@{ FullName = $_.FullName; Name = $_.Name; Reason = "canonical_t_axioms" }) | Out-Null
        }
}

foreach ($r in $SourceRoots) {
    if (-not (Test-Path $r)) { continue }
    Get-ChildItem -Path $r -Recurse -File -Filter "*axiom*" -ErrorAction SilentlyContinue |
        Where-Object { ($exts -contains $_.Extension.ToLowerInvariant()) -and ($_.FullName -notmatch $exclude) } |
        ForEach-Object {
            $candidates.Add([pscustomobject]@{ FullName = $_.FullName; Name = $_.Name; Reason = "axiom_named_root" }) | Out-Null
        }
}

$candidates = $candidates | Sort-Object FullName -Unique
Write-Output ("CANDIDATES=" + $candidates.Count)

$hashMap = @{}
$records = @()
$seqRows = @()
$catCounts = @{}

foreach ($c in $candidates) {
    if (-not (Test-Path $c.FullName)) { continue }
    $hash = (Get-FileHash -Path $c.FullName -Algorithm SHA256).Hash
    $dup = $hashMap.ContainsKey($hash)
    $dupOf = ""
    if ($dup) { $dupOf = $hashMap[$hash] } else { $hashMap[$hash] = $c.FullName }

    $base = [IO.Path]::GetFileNameWithoutExtension($c.Name)
    $seq = $null
    $token = ""
    $m = [regex]::Match($base, "^(\d{3})_([^_]+)")
    if ($m.Success) {
        $seq = [int]$m.Groups[1].Value
        $token = $m.Groups[2].Value
    }

    $cat = Get-CategoryFromToken -Token $token -PathLower $c.FullName.ToLowerInvariant()
    if (-not $catCounts.ContainsKey($cat)) { $catCounts[$cat] = 0 }
    $catCounts[$cat] += 1

    $safe = ($c.Name -replace "[^\w\.\- ]","_" -replace "\s+","-")
    $h8 = $hash.Substring(0,8)

    if (-not $dup) {
        Copy-Item -Path $c.FullName -Destination (Join-Path $rawDir ("{0}__{1}" -f $h8,$safe)) -Force

        $cd = Join-Path $catRoot $cat
        New-Item -ItemType Directory -Path $cd -Force | Out-Null
        Copy-Item -Path $c.FullName -Destination (Join-Path $cd ("{0}__{1}" -f $h8,$safe)) -Force

        if ($null -ne $seq) {
            $cn = "{0:D3}__{1}" -f $seq,$safe
            $cp = Join-Path $canonDir $cn
            if (Test-Path $cp) {
                $cn = "{0:D3}__{1}__{2}" -f $seq,$h8,$safe
                $cp = Join-Path $canonDir $cn
            }
            Copy-Item -Path $c.FullName -Destination $cp -Force
            $seqRows += [pscustomobject]@{ seq = $seq; token = $token; name = $c.Name; source = $c.FullName }
        }
    }

    $records += [pscustomobject]@{
        source_path = $c.FullName
        reason = $c.Reason
        sha256 = $hash
        duplicate = $dup
        duplicate_of = $dupOf
        seq = $seq
        token = $token
        category = $cat
    }
}

$map = Join-Path $metaDir ("AXIOM_SOURCE_MAP_{0}.csv" -f $ts)
$records | Export-Csv -Path $map -NoTypeInformation -Encoding UTF8

$seqIdx = Join-Path $metaDir "00_INDEX_CANONICAL_SEQUENTIAL.md"
$seqLines = @("# Canonical Sequential Index","",("Generated: " + $ts),"")
foreach ($r in ($seqRows | Sort-Object seq, name)) {
    $seqLines += ("- {0:D3} | {1} | {2}" -f $r.seq,$r.token,$r.name)
}
Set-Content -Path $seqIdx -Value $seqLines -Encoding UTF8

$catIdx = Join-Path $metaDir "00_INDEX_CATEGORIES.md"
$catLines = @("# Category Index","",("Generated: " + $ts),"")
foreach ($k in ($catCounts.Keys | Sort-Object)) {
    $catLines += ("- {0}: {1}" -f $k, $catCounts[$k])
}
Set-Content -Path $catIdx -Value $catLines -Encoding UTF8

$uniq = ($records | Where-Object { -not $_.duplicate }).Count
$dups = ($records | Where-Object { $_.duplicate }).Count
$sum = Join-Path $metaDir "BUILD_SUMMARY.md"
Set-Content -Path $sum -Value @(
    "# Build Summary",
    "",
    ("Generated: " + $ts),
    ("Destination: " + $dest),
    ("Candidate files: " + $records.Count),
    ("Unique files copied: " + $uniq),
    ("Duplicates skipped by hash: " + $dups)
) -Encoding UTF8

$zip = Join-Path $docs ("Axioms_Production_Vault_{0}.zip" -f $ts)
Compress-Archive -Path $dest -DestinationPath $zip -CompressionLevel Optimal -Force

$tZip = ""
$tFolder = ""
if (Test-Path $TProductionAxiomsPath) {
    $tZip = Join-Path $TProductionAxiomsPath ([IO.Path]::GetFileName($zip))
    Copy-Item -Path $zip -Destination $tZip -Force
    $tFolder = Join-Path $TProductionAxiomsPath ([IO.Path]::GetFileName($dest))
    if (Test-Path $tFolder) { Remove-Item -Path $tFolder -Recurse -Force }
    Copy-Item -Path $dest -Destination $tFolder -Recurse -Force
}

Write-Output ("DEST_ROOT=" + $dest)
Write-Output ("ZIP_PATH=" + $zip)
if ($tZip) { Write-Output ("T_ZIP_PATH=" + $tZip) }
if ($tFolder) { Write-Output ("T_FOLDER_PATH=" + $tFolder) }
Write-Output ("UNIQUE_FILES=" + $uniq)
Write-Output ("DUPLICATES=" + $dups)
