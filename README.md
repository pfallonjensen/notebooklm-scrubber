# NotebookLM Logo Remover

**Remove the NotebookLM watermark from your exported PDF slides.**

When you export slides from Google's NotebookLM, they include a small logo in the corner. This tool removes it automatically.

---

## Quick Install (Mac)

Open **Terminal** (search for "Terminal" in Spotlight) and paste this:

```bash
curl -fsSL https://raw.githubusercontent.com/pfallonjensen/notebooklm-scrubber/main/install.sh | bash
```

Follow the prompts. That's it!

---

## Quick Install (Windows)

Open **PowerShell** (search for "PowerShell" in the Start menu) and paste this:

```powershell
irm https://raw.githubusercontent.com/pfallonjensen/notebooklm-scrubber/main/install.ps1 | iex
```

Follow the prompts. That's it!

> **Tip:** When it asks for your watch folder path, open File Explorer, navigate to the folder, click the address bar at the top, and copy the full path (Ctrl+C).

---

## How It Works

1. **Export** a PDF from NotebookLM
2. **Drop** the PDF into your watch folder (you pick this during setup)
3. **Done!** A clean version appears automatically (`yourfile_clean.pdf`)

The clean version has no logo. The original file is kept unchanged.

---

## Requirements

- **Mac or Windows**
- **Python 3** (usually pre-installed on Mac; [download for Windows](https://www.python.org/downloads/))

> **Windows users:** When installing Python, make sure to check **"Add Python to PATH"** during installation!

---

## Manual Install

If the quick install doesn't work:

1. Download this project (green "Code" button → "Download ZIP")
2. Unzip it somewhere (like your Documents folder)

**Mac:**
```bash
cd ~/Documents/notebooklm-scrubber-main
chmod +x setup.sh
./setup.sh
```

**Windows (PowerShell):**
```powershell
cd "$env:USERPROFILE\Documents\notebooklm-scrubber-main"
powershell -ExecutionPolicy Bypass -File install.ps1
```

---

## Processing a Single File

Don't want automatic processing? Just run this in your terminal:

**Mac:**
```bash
python3 scrub-notebooklm-logo.py yourfile.pdf
```

**Windows:**
```powershell
python scrub-notebooklm-logo.py yourfile.pdf
```

Creates `yourfile_clean.pdf` in the same folder.

---

## Troubleshooting

**"Python not found"**
→ Install Python from [python.org](https://www.python.org/downloads/)
→ **Windows:** Make sure "Add Python to PATH" was checked during install. If not, reinstall Python and check it.

**Clean file doesn't appear**
→ Wait a few seconds (especially if using Google Drive or OneDrive)
→ Check the log file: `~/notebooklm-scrubber/scrub.log` (Mac) or `%USERPROFILE%\notebooklm-scrubber\scrub.log` (Windows)

**Logo still visible**
→ The tool is tuned for standard NotebookLM exports. If Google changes the format, the position may need adjusting.

**Windows: "Execution Policy" error**
→ Run PowerShell as Administrator and enter: `Set-ExecutionPolicy RemoteSigned`
→ Or use the `-ExecutionPolicy Bypass` flag as shown in the manual install section.

---

## Uninstall

**Mac:**
```bash
# Stop the automatic processing
launchctl unload ~/Library/LaunchAgents/com.notebooklm-scrubber.plist

# Delete the files
rm -rf ~/notebooklm-scrubber
rm ~/Library/LaunchAgents/com.notebooklm-scrubber.plist
```

**Windows (PowerShell as Administrator):**
```powershell
# Stop the automatic processing
Unregister-ScheduledTask -TaskName "NotebookLM-Scrubber" -Confirm:$false

# Remove environment variable
[Environment]::SetEnvironmentVariable("NOTEBOOKLM_WATCH_DIR", $null, "User")

# Delete the files
Remove-Item -Recurse -Force "$env:USERPROFILE\notebooklm-scrubber"
```

---

## For Developers

<details>
<summary>Click to expand technical details</summary>

### How the logo removal works

The tool creates a gradient overlay using **bilinear interpolation**:

1. Samples colors from 4 corners around the logo area (with 5×5 pixel averaging)
2. Generates a smooth gradient that matches the surrounding background
3. Overlays it on the PDF, covering the logo

This handles solid colors, gradients, and images reasonably well.

### File structure

```
notebooklm-scrubber/
├── scrub-notebooklm-logo.py      # Core Python script
├── watch-and-scrub.sh            # Folder watcher (Mac)
├── watch-and-scrub.ps1           # Folder watcher (Windows)
├── install.sh                    # One-line installer (Mac)
├── install.ps1                   # One-line installer (Windows)
├── setup.sh                      # Local setup script (Mac)
├── com.notebooklm-scrubber.plist.template
├── requirements.txt
└── README.md
```

### Automation details

- **Mac:** Uses a LaunchAgent (`WatchPaths`) that triggers instantly when the folder changes
- **Windows:** Uses a Scheduled Task that checks the folder every 5 minutes

### Logo position (if you need to adjust)

In `scrub-notebooklm-logo.py`:
```python
LOGO_LEFT = 1269   # Move left: decrease, Move right: increase
LOGO_TOP = 747     # Move up: decrease, Move down: increase
```

### Dependencies

- PyMuPDF (PDF manipulation)
- Pillow (image generation)

</details>

---

## License

MIT - Use it however you want.
