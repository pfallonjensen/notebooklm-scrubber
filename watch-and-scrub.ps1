# NotebookLM Logo Scrubber - Watch and Process Script (Windows)
# Watches a folder for new PDFs and removes the NotebookLM watermark

param(
    [string]$WatchDir
)

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$VenvPython = Join-Path $ScriptDir "venv\Scripts\python.exe"
$LogFile = Join-Path $ScriptDir "scrub.log"
$ProcessedFile = Join-Path $ScriptDir ".processed_files"

# Use param, env var, or default
if (-not $WatchDir) {
    $WatchDir = $env:NOTEBOOKLM_WATCH_DIR
}
if (-not $WatchDir) {
    $WatchDir = Join-Path $env:USERPROFILE "Documents\NotebookLM-PDFs"
}

# Ensure processed file exists
if (-not (Test-Path $ProcessedFile)) {
    New-Item -Path $ProcessedFile -ItemType File -Force | Out-Null
}

function Write-Log {
    param([string]$Message)
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    "[$timestamp] $Message" | Add-Content -Path $LogFile
}

function Get-FileHashString {
    param([string]$FilePath)
    $bytes = [System.Text.Encoding]::UTF8.GetBytes($FilePath)
    $sha = [System.Security.Cryptography.SHA1]::Create()
    $hash = $sha.ComputeHash($bytes)
    return ($hash | ForEach-Object { $_.ToString("x2") }) -join ''
}

function Wait-ForFileReady {
    param([string]$FilePath, [int]$MaxWait = 30)
    $waited = 0
    while ($waited -lt $MaxWait) {
        $size1 = (Get-Item $FilePath).Length
        Start-Sleep -Seconds 2
        $size2 = (Get-Item $FilePath).Length
        if ($size1 -eq $size2 -and $size1 -gt 0) {
            return $true
        }
        $waited += 2
        Write-Log "Waiting for file to sync: $(Split-Path -Leaf $FilePath) (${waited}s)"
    }
    return $false
}

Write-Log "=== Starting NotebookLM scrubber ==="
Write-Log "Watching: $WatchDir"

if (-not (Test-Path $WatchDir)) {
    Write-Log "ERROR: Watch directory does not exist: $WatchDir"
    Write-Error "Watch directory does not exist: $WatchDir"
    exit 1
}

$processedHashes = Get-Content $ProcessedFile -ErrorAction SilentlyContinue

Get-ChildItem -Path $WatchDir -Filter "*.pdf" -File | ForEach-Object {
    $pdfFile = $_.FullName

    # Skip _clean files
    if ($pdfFile -match '_clean\.pdf$') { return }

    # Check if clean version already exists
    $baseName = [System.IO.Path]::GetFileNameWithoutExtension($pdfFile)
    $dir = [System.IO.Path]::GetDirectoryName($pdfFile)
    $cleanFile = Join-Path $dir "${baseName}_clean.pdf"

    if (Test-Path $cleanFile) { return }

    # Skip if already processed
    $fileHash = Get-FileHashString $pdfFile
    if ($processedHashes -contains $fileHash) { return }

    Write-Log "Processing: $($_.Name)"

    # Wait for file to finish syncing
    if (-not (Wait-ForFileReady $pdfFile)) {
        Write-Log "SKIP: File still syncing after timeout: $($_.Name)"
        return
    }

    # Run the scrubber
    $result = & $VenvPython (Join-Path $ScriptDir "scrub-notebooklm-logo.py") $pdfFile $cleanFile 2>&1
    $result | Add-Content -Path $LogFile

    if ($LASTEXITCODE -eq 0) {
        Write-Log "SUCCESS: Created $(Split-Path -Leaf $cleanFile)"
        $fileHash | Add-Content -Path $ProcessedFile
    } else {
        Write-Log "ERROR: Failed to process $($_.Name)"
    }
}

Write-Log "=== Scrubber run complete ==="
