param(
    [string]$TargetPath = $PSScriptRoot,
    [string]$OutputDir = "",
    [bool]$Recurse = $true,
    [int]$MaxCharsPerFile = 0,
    [switch]$IncludeBinaryBase64,
    [string[]]$ExcludeDirs = @(
        ".git",
        ".obsidian",
        ".trash",
        ".vscode",
        "node_modules",
        "__pycache__",
        ".venv",
        "venv"
    ),
    [string[]]$IncludeExtensions = @(
        ".md",".txt",".csv",".tsv",".json",".jsonl",".yaml",".yml",".toml",".ini",".xml",".html",".htm",
        ".ps1",".psm1",".bat",".cmd",".py",".js",".ts",".css",".sql",".r",".ipynb",
        ".docx",".pdf",".doc"
    )
)

$ErrorActionPreference = "Stop"

function Get-NowStamp {
    return (Get-Date -Format "yyyyMMdd_HHmmss")
}

function Get-NormalizedPath([string]$PathValue) {
    return ([System.IO.Path]::GetFullPath($PathValue))
}

function Should-SkipPath {
    param(
        [string]$FullPath,
        [string]$OutputRoot,
        [string[]]$Excluded
    )

    if ($FullPath.StartsWith($OutputRoot, [System.StringComparison]::OrdinalIgnoreCase)) {
        return $true
    }

    foreach ($name in $Excluded) {
        $rx = "(^|[\\/])" + [regex]::Escape($name) + "($|[\\/])"
        if ($FullPath -match $rx) {
            return $true
        }
    }
    return $false
}

function Get-LanguageFromExtension([string]$Ext) {
    $map = @{
        ".md"="markdown"; ".txt"="text"; ".csv"="csv"; ".tsv"="tsv"; ".json"="json"; ".jsonl"="json";
        ".yaml"="yaml"; ".yml"="yaml"; ".toml"="toml"; ".ini"="ini"; ".xml"="xml"; ".html"="html"; ".htm"="html";
        ".ps1"="powershell"; ".psm1"="powershell"; ".bat"="bat"; ".cmd"="bat"; ".py"="python"; ".js"="javascript";
        ".ts"="typescript"; ".css"="css"; ".sql"="sql"; ".r"="r"; ".ipynb"="json"; ".docx"="text"; ".pdf"="text"; ".doc"="text"
    }
    if ($map.ContainsKey($Ext)) { return $map[$Ext] }
    return "text"
}

function Read-TextFile([string]$PathValue) {
    try { return (Get-Content -Path $PathValue -Raw -Encoding UTF8) } catch {}
    try { return (Get-Content -Path $PathValue -Raw) } catch {}
    return $null
}

function Read-DocxText([string]$PathValue) {
    try {
        Add-Type -AssemblyName "System.IO.Compression" -ErrorAction SilentlyContinue | Out-Null
        Add-Type -AssemblyName "System.IO.Compression.FileSystem" -ErrorAction SilentlyContinue | Out-Null

        $fileStream = [System.IO.File]::OpenRead($PathValue)
        try {
            $zip = New-Object System.IO.Compression.ZipArchive($fileStream, [System.IO.Compression.ZipArchiveMode]::Read, $false)
            try {
                $entry = $zip.GetEntry("word/document.xml")
                if ($null -eq $entry) { return $null }
                $stream = $entry.Open()
                try {
                    $reader = New-Object System.IO.StreamReader($stream)
                    $xmlRaw = $reader.ReadToEnd()
                    $reader.Dispose()
                } finally {
                    $stream.Dispose()
                }
            } finally {
                $zip.Dispose()
            }
        } finally {
            $fileStream.Dispose()
        }

        $text = [regex]::Replace($xmlRaw, "<w:p[^>]*>", "`n")
        $text = [regex]::Replace($text, "<[^>]+>", " ")
        $text = [System.Net.WebUtility]::HtmlDecode($text)
        $text = [regex]::Replace($text, "[ \t]+", " ")
        $text = [regex]::Replace($text, "`n{3,}", "`n`n")
        return $text.Trim()
    } catch {
        return $null
    }
}

function Read-PdfText([string]$PathValue) {
    $tmpTxt = Join-Path $env:TEMP ("lossless_pdf_" + [guid]::NewGuid().ToString() + ".txt")
    $tmpPy = Join-Path $env:TEMP ("lossless_pdf_" + [guid]::NewGuid().ToString() + ".py")

    try {
        $pdfToText = Get-Command "pdftotext" -ErrorAction SilentlyContinue
        if ($null -ne $pdfToText) {
            & $pdfToText.Source "-layout" $PathValue $tmpTxt 2>$null | Out-Null
            if (Test-Path $tmpTxt) {
                $t = Read-TextFile $tmpTxt
                if ($null -ne $t -and $t.Trim().Length -gt 0) {
                    return @{ Text = $t; Method = "pdftotext" }
                }
            }
        }

        $python = Get-Command "python" -ErrorAction SilentlyContinue
        if ($null -ne $python) {
            $py = @'
import sys
from pathlib import Path
p = Path(sys.argv[1])
out = Path(sys.argv[2])
Reader = None
try:
    from pypdf import PdfReader as Reader
except Exception:
    try:
        from PyPDF2 import PdfReader as Reader
    except Exception:
        pass
if Reader is None:
    raise SystemExit(3)
r = Reader(str(p))
parts = []
for i, page in enumerate(r.pages, start=1):
    try:
        txt = page.extract_text() or ""
    except Exception:
        txt = ""
    parts.append(f"\n\n--- PAGE {i} ---\n{txt}")
out.write_text("".join(parts), encoding="utf-8")
'@
            Set-Content -Path $tmpPy -Value $py -Encoding UTF8
            & $python.Source $tmpPy $PathValue $tmpTxt 2>$null | Out-Null
            if (Test-Path $tmpTxt) {
                $t = Read-TextFile $tmpTxt
                if ($null -ne $t -and $t.Trim().Length -gt 0) {
                    return @{ Text = $t; Method = "python-pypdf" }
                }
            }
        }

        return $null
    } finally {
        if (Test-Path $tmpTxt) { Remove-Item -Path $tmpTxt -Force -ErrorAction SilentlyContinue }
        if (Test-Path $tmpPy) { Remove-Item -Path $tmpPy -Force -ErrorAction SilentlyContinue }
    }
}

function Write-MdSection {
    param(
        [System.Text.StringBuilder]$Builder,
        [int]$Index,
        [string]$RelPath,
        [string]$Ext,
        [long]$SizeBytes,
        [datetime]$ModifiedUtc,
        [string]$Sha256,
        [string]$Method,
        [string]$Content
    )
    $lang = Get-LanguageFromExtension $Ext
    [void]$Builder.AppendLine("## File " + ("{0:D4}" -f $Index) + ": " + $RelPath)
    [void]$Builder.AppendLine("")
    [void]$Builder.AppendLine("- Extension: " + $Ext)
    [void]$Builder.AppendLine("- Size: " + $SizeBytes + " bytes")
    [void]$Builder.AppendLine("- Modified (UTC): " + $ModifiedUtc.ToString("yyyy-MM-dd HH:mm:ss"))
    [void]$Builder.AppendLine("- SHA256: " + $Sha256)
    [void]$Builder.AppendLine("- Extraction: " + $Method)
    [void]$Builder.AppendLine("")
    [void]$Builder.AppendLine('```' + $lang)
    [void]$Builder.AppendLine($Content)
    [void]$Builder.AppendLine('```')
    [void]$Builder.AppendLine("")
    [void]$Builder.AppendLine("---")
    [void]$Builder.AppendLine("")
}

if ([string]::IsNullOrWhiteSpace($TargetPath)) {
    throw "TargetPath is empty."
}
if (-not (Test-Path $TargetPath)) {
    throw "TargetPath not found: $TargetPath"
}

$targetRoot = Get-NormalizedPath $TargetPath
$timestamp = Get-NowStamp
if ([string]::IsNullOrWhiteSpace($OutputDir)) {
    $OutputDir = Join-Path $targetRoot ("_LOSSLESS_SUMMARY_" + $timestamp)
}
$outputRoot = Get-NormalizedPath $OutputDir
New-Item -ItemType Directory -Path $outputRoot -Force | Out-Null

$summaryPath = Join-Path $outputRoot ("LOSSLESS_SUMMARY_" + $timestamp + ".md")
$manifestPath = Join-Path $outputRoot ("LOSSLESS_MANIFEST_" + $timestamp + ".csv")
$errorsPath = Join-Path $outputRoot ("LOSSLESS_ERRORS_" + $timestamp + ".log")
$zipPath = Join-Path $outputRoot ("LOSSLESS_PACK_" + $timestamp + ".zip")

$includeSet = New-Object "System.Collections.Generic.HashSet[string]" ([System.StringComparer]::OrdinalIgnoreCase)
foreach ($ext in $IncludeExtensions) {
    if ([string]::IsNullOrWhiteSpace($ext)) { continue }
    if ($ext.StartsWith(".")) { [void]$includeSet.Add($ext.ToLowerInvariant()) }
    else { [void]$includeSet.Add(("." + $ext).ToLowerInvariant()) }
}

if ($Recurse) {
    $allFiles = Get-ChildItem -Path $targetRoot -File -Recurse -Force -ErrorAction Stop
} else {
    $allFiles = Get-ChildItem -Path $targetRoot -File -Force -ErrorAction Stop
}

$files = @()
foreach ($f in $allFiles) {
    $full = Get-NormalizedPath $f.FullName
    if (Should-SkipPath -FullPath $full -OutputRoot $outputRoot -Excluded $ExcludeDirs) { continue }
    $ext = $f.Extension.ToLowerInvariant()
    if (-not $includeSet.Contains($ext)) { continue }
    $files += $f
}

$files = $files | Sort-Object FullName

$sb = New-Object System.Text.StringBuilder
[void]$sb.AppendLine("# Lossless Summary Bundle")
[void]$sb.AppendLine("")
[void]$sb.AppendLine("- Source Root: " + $targetRoot)
[void]$sb.AppendLine("- Generated (UTC): " + (Get-Date).ToUniversalTime().ToString("yyyy-MM-dd HH:mm:ss"))
[void]$sb.AppendLine("- Files Included: " + $files.Count)
[void]$sb.AppendLine("- Mode: lossless (full extracted content unless unsupported)")
[void]$sb.AppendLine("")
[void]$sb.AppendLine("---")
[void]$sb.AppendLine("")

$manifestRows = @()
$errors = @()
$i = 0

foreach ($f in $files) {
    $i++
    $ext = $f.Extension.ToLowerInvariant()
    $rel = $f.FullName.Substring($targetRoot.Length).TrimStart('\','/')
    $hash = (Get-FileHash -Path $f.FullName -Algorithm SHA256).Hash
    $method = ""
    $content = $null

    try {
        switch ($ext) {
            ".docx" {
                $content = Read-DocxText $f.FullName
                if ($null -eq $content) {
                    $method = "docx-unreadable"
                    $content = "[Could not extract DOCX text.]"
                } else {
                    $method = "docx-xml"
                }
            }
            ".pdf" {
                $res = Read-PdfText $f.FullName
                if ($null -eq $res) {
                    $method = "pdf-unreadable"
                    $content = "[Could not extract PDF text. Install pdftotext or python+pypdf for extraction.]"
                } else {
                    $method = $res.Method
                    $content = $res.Text
                }
            }
            ".doc" {
                $method = "doc-unsupported"
                if ($IncludeBinaryBase64) {
                    $bytes = [System.IO.File]::ReadAllBytes($f.FullName)
                    $content = [Convert]::ToBase64String($bytes)
                    $method = "doc-base64"
                } else {
                    $content = "[Binary .doc file. Re-run with -IncludeBinaryBase64 to embed content.]"
                }
            }
            default {
                $content = Read-TextFile $f.FullName
                if ($null -eq $content) {
                    if ($IncludeBinaryBase64) {
                        $bytes = [System.IO.File]::ReadAllBytes($f.FullName)
                        $content = [Convert]::ToBase64String($bytes)
                        $method = "binary-base64"
                    } else {
                        $content = "[Could not read as text. Re-run with -IncludeBinaryBase64 to embed content.]"
                        $method = "text-read-failed"
                    }
                } else {
                    $method = "raw-text"
                }
            }
        }

        if ($MaxCharsPerFile -gt 0 -and $content.Length -gt $MaxCharsPerFile) {
            $content = $content.Substring(0, $MaxCharsPerFile) + "`n`n[TRUNCATED by MaxCharsPerFile]"
            $method = $method + "+truncated"
        }

        Write-MdSection -Builder $sb -Index $i -RelPath $rel -Ext $ext -SizeBytes $f.Length -ModifiedUtc ($f.LastWriteTimeUtc) -Sha256 $hash -Method $method -Content $content
    } catch {
        $err = "ERROR | " + $rel + " | " + $_.Exception.Message
        $errors += $err
        $fallback = "[Error while extracting file content. See LOSSLESS_ERRORS log.]"
        Write-MdSection -Builder $sb -Index $i -RelPath $rel -Ext $ext -SizeBytes $f.Length -ModifiedUtc ($f.LastWriteTimeUtc) -Sha256 $hash -Method "error" -Content $fallback
    }

    $manifestRows += [pscustomobject]@{
        index = $i
        relative_path = $rel
        extension = $ext
        bytes = $f.Length
        modified_utc = $f.LastWriteTimeUtc.ToString("yyyy-MM-dd HH:mm:ss")
        sha256 = $hash
        extraction = $method
    }
}

Set-Content -Path $summaryPath -Value $sb.ToString() -Encoding UTF8
$manifestRows | Export-Csv -Path $manifestPath -NoTypeInformation -Encoding UTF8

if ($errors.Count -eq 0) {
    Set-Content -Path $errorsPath -Value "No extraction errors." -Encoding UTF8
} else {
    Set-Content -Path $errorsPath -Value ($errors -join "`n") -Encoding UTF8
}

Compress-Archive -Path $summaryPath,$manifestPath,$errorsPath -DestinationPath $zipPath -CompressionLevel Optimal -Force

Write-Output ("TARGET=" + $targetRoot)
Write-Output ("OUTPUT=" + $outputRoot)
Write-Output ("SUMMARY=" + $summaryPath)
Write-Output ("MANIFEST=" + $manifestPath)
Write-Output ("ERRORS=" + $errorsPath)
Write-Output ("ZIP=" + $zipPath)
Write-Output ("FILES_PROCESSED=" + $files.Count)
