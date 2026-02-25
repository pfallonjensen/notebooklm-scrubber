# =============================================================================
# NotebookLM Logo Scrubber - One-Click Installer (Windows)
#
# Run this with:
#   curl -fsSL https://raw.githubusercontent.com/pfallonjensen/notebooklm-scrubber/main/install.ps1 | powershell -
#
# Or in PowerShell directly:
#   iwr -useb https://raw.githubusercontent.com/pfallonjensen/notebooklm-scrubber/main/install.ps1 | iex
# =============================================================================

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "========================================" -ForegroundColor White
Write-Host "  NotebookLM Logo Remover - Installer"   -ForegroundColor White
Write-Host "========================================" -ForegroundColor White
Write-Host ""

# ── Check requirements ──────────────────────────────────────────────────────

function Test-Requirements {
    Write-Host "Checking requirements..." -ForegroundColor Cyan

    # Check for Python 3
    $python = $null
    foreach ($cmd in @("python", "python3", "py")) {
        try {
            $ver = & $cmd --version 2>&1
            if ($ver -match "Python 3") {
                $python = $cmd
                break
            }
        } catch {}
    }

    if (-not $python) {
        Write-Host "Error: Python 3 is required but not installed." -ForegroundColor Red
        Write-Host ""
        Write-Host "Please install Python 3 first:"
        Write-Host "  Download from https://www.python.org/downloads/"
        Write-Host "  IMPORTANT: Check 'Add Python to PATH' during installation!"
        exit 1
    }

    $script:PythonCmd = $python
    Write-Host "  Python found: $python ($ver)" -ForegroundColor Green
    Write-Host ""
}

# ── Download the project ────────────────────────────────────────────────────

function Get-Project {
    $script:InstallDir = Join-Path $env:USERPROFILE "notebooklm-scrubber"

    Write-Host "Downloading NotebookLM Scrubber..." -ForegroundColor Cyan

    if (Test-Path $script:InstallDir) {
        Write-Host "Installation folder already exists at $($script:InstallDir)"
        $reply = Read-Host "Remove it and reinstall? (y/n)"
        if ($reply -match '^[Yy]') {
            Remove-Item -Recurse -Force $script:InstallDir
        } else {
            Write-Host "Keeping existing installation. Exiting."
            exit 0
        }
    }

    # Try git first, fall back to downloading zip
    $useGit = $false
    try {
        $null = & git --version 2>&1
        $useGit = $true
    } catch {}

    if ($useGit) {
        & git clone --quiet https://github.com/pfallonjensen/notebooklm-scrubber.git $script:InstallDir
    } else {
        $zipUrl = "https://github.com/pfallonjensen/notebooklm-scrubber/archive/main.zip"
        $zipFile = Join-Path $env:TEMP "notebooklm-scrubber.zip"
        $extractDir = Join-Path $env:TEMP "notebooklm-scrubber-extract"

        Invoke-WebRequest -Uri $zipUrl -OutFile $zipFile -UseBasicParsing
        if (Test-Path $extractDir) { Remove-Item -Recurse -Force $extractDir }
        Expand-Archive -Path $zipFile -DestinationPath $extractDir
        Move-Item (Join-Path $extractDir "notebooklm-scrubber-main") $script:InstallDir
        Remove-Item $zipFile -Force
        Remove-Item $extractDir -Recurse -Force
    }

    Write-Host "  Downloaded to $($script:InstallDir)" -ForegroundColor Green
    Write-Host ""
}

# ── Get watch folder from user ──────────────────────────────────────────────

function Get-WatchFolder {
    Write-Host "Where do you want to drop your NotebookLM PDFs?" -ForegroundColor White
    Write-Host ""
    Write-Host "This is the folder you'll use to process PDFs."
    Write-Host "Drop a PDF in -> get a clean PDF out (without the logo)."
    Write-Host ""
    Write-Host "Examples:"
    Write-Host "  $env:USERPROFILE\Documents\NotebookLM"
    Write-Host "  $env:USERPROFILE\Desktop\NotebookLM-PDFs"
    Write-Host "  $env:USERPROFILE\Google Drive\NotebookLM"
    Write-Host ""

    $default = Join-Path $env:USERPROFILE "Documents\NotebookLM-PDFs"
    $input = Read-Host "Folder path (press Enter for $default)"

    if ([string]::IsNullOrWhiteSpace($input)) {
        $script:WatchDir = $default
    } else {
        $script:WatchDir = $input
    }

    if (-not (Test-Path $script:WatchDir)) {
        Write-Host ""
        $reply = Read-Host "This folder doesn't exist. Create it? (y/n)"
        if ($reply -match '^[Yy]') {
            New-Item -ItemType Directory -Path $script:WatchDir -Force | Out-Null
            Write-Host "  Created folder" -ForegroundColor Green
        } else {
            Write-Host "Please create the folder first and run this installer again." -ForegroundColor Red
            exit 1
        }
    }

    Write-Host ""
    Write-Host "  Watch folder: $($script:WatchDir)" -ForegroundColor Green
    Write-Host ""
}

# ── Set up Python environment ───────────────────────────────────────────────

function Install-PythonEnv {
    Write-Host "Setting up Python environment..." -ForegroundColor Cyan

    Push-Location $script:InstallDir

    & $script:PythonCmd -m venv venv

    $pipPath = Join-Path $script:InstallDir "venv\Scripts\pip.exe"
    & $pipPath install --quiet --upgrade pip
    & $pipPath install --quiet pymupdf pillow

    Pop-Location

    Write-Host "  Python packages installed" -ForegroundColor Green
    Write-Host ""
}

# ── Set up Windows Task Scheduler automation ────────────────────────────────

function Install-ScheduledTask {
    Write-Host "Setting up automatic processing..." -ForegroundColor Cyan

    $taskName = "NotebookLM-Scrubber"
    $watchScript = Join-Path $script:InstallDir "watch-and-scrub.ps1"

    # Remove existing task if present
    $existing = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
    if ($existing) {
        Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
    }

    # Build the action: run PowerShell with the watch script
    $action = New-ScheduledTaskAction `
        -Execute "powershell.exe" `
        -Argument "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$watchScript`"" `
        -WorkingDirectory $script:InstallDir

    # Trigger 1: At user logon
    $triggerLogon = New-ScheduledTaskTrigger -AtLogOn

    # Trigger 2: Every 5 minutes (repetition)
    $triggerRepeat = New-ScheduledTaskTrigger -Once -At (Get-Date) `
        -RepetitionInterval (New-TimeSpan -Minutes 5) `
        -RepetitionDuration (New-TimeSpan -Days 365)

    # Settings
    $settings = New-ScheduledTaskSettingsSet `
        -AllowStartIfOnBatteries `
        -DontStopIfGoingOnBatteries `
        -StartWhenAvailable `
        -ExecutionTimeLimit (New-TimeSpan -Minutes 5)

    # Set the watch dir as environment variable for the task
    $envVar = "NOTEBOOKLM_WATCH_DIR=$($script:WatchDir)"

    # Register the task
    try {
        Register-ScheduledTask `
            -TaskName $taskName `
            -Action $action `
            -Trigger $triggerLogon, $triggerRepeat `
            -Settings $settings `
            -Description "Watches for NotebookLM PDFs and removes the logo watermark" `
            | Out-Null

        # Set the environment variable persistently for the current user
        [Environment]::SetEnvironmentVariable("NOTEBOOKLM_WATCH_DIR", $script:WatchDir, "User")

        Write-Host "  Scheduled Task created (runs every 5 minutes)" -ForegroundColor Green
    } catch {
        Write-Host "  Could not create Scheduled Task (may need admin rights)." -ForegroundColor Yellow
        Write-Host "  Setting up environment variable for manual use instead." -ForegroundColor Yellow
        [Environment]::SetEnvironmentVariable("NOTEBOOKLM_WATCH_DIR", $script:WatchDir, "User")
    }

    Write-Host ""
}

# ── Run initial scan ────────────────────────────────────────────────────────

function Invoke-InitialScan {
    # Run once now to process any existing PDFs
    $watchScript = Join-Path $script:InstallDir "watch-and-scrub.ps1"
    $env:NOTEBOOKLM_WATCH_DIR = $script:WatchDir
    try {
        & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $watchScript 2>&1 | Out-Null
    } catch {}
}

# ── Print success ──────────────────────────────────────────────────────────

function Show-Success {
    Write-Host "========================================" -ForegroundColor White
    Write-Host "  Installation Complete!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor White
    Write-Host ""
    Write-Host "How to use:" -ForegroundColor White
    Write-Host ""
    Write-Host "  1. Export a PDF from NotebookLM"
    Write-Host "  2. Drop it in: $($script:WatchDir)"
    Write-Host "  3. A clean version appears automatically!"
    Write-Host "     (filename_clean.pdf - without the logo)"
    Write-Host ""
    Write-Host "That's it! The logo is removed automatically." -ForegroundColor White
    Write-Host ""
    Write-Host "---"
    Write-Host ""
    Write-Host "Manual usage (for single files):"
    $venvPython = Join-Path $script:InstallDir "venv\Scripts\python.exe"
    $scrubScript = Join-Path $script:InstallDir "scrub-notebooklm-logo.py"
    Write-Host "  & `"$venvPython`" `"$scrubScript`" yourfile.pdf"
    Write-Host ""
    Write-Host "Logs (if something goes wrong):"
    Write-Host "  $(Join-Path $script:InstallDir 'scrub.log')"
    Write-Host ""
}

# ── Main ────────────────────────────────────────────────────────────────────

Test-Requirements
Get-Project
Get-WatchFolder
Install-PythonEnv
Install-ScheduledTask
Invoke-InitialScan
Show-Success
