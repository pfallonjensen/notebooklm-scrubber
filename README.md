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

## How It Works

1. **Export** a PDF from NotebookLM
2. **Drop** the PDF into your watch folder (you pick this during setup)
3. **Done!** A clean version appears automatically (`yourfile_clean.pdf`)

The clean version has no logo. The original file is kept unchanged.

---

## Requirements

- **Mac** (for automatic processing)
- **Python 3** (usually pre-installed on Mac)

Don't have Python? Download it from [python.org](https://www.python.org/downloads/)

---

## Manual Install

If the quick install doesn't work:

1. Download this project (green "Code" button → "Download ZIP")
2. Unzip it somewhere (like your Documents folder)
3. Open Terminal and run:
   ```bash
   cd ~/Documents/notebooklm-scrubber-main
   chmod +x setup.sh
   ./setup.sh
   ```

---

## Processing a Single File

Don't want automatic processing? Just run this in Terminal:

```bash
python3 scrub-notebooklm-logo.py yourfile.pdf
```

Creates `yourfile_clean.pdf` in the same folder.

---

## Troubleshooting

**"Python not found"**
→ Install Python from [python.org](https://www.python.org/downloads/)

**Clean file doesn't appear**
→ Wait a few seconds (especially if using Google Drive)
→ Check the log file: `~/notebooklm-scrubber/scrub.log`

**Logo still visible**
→ The tool is tuned for standard NotebookLM exports. If Google changes the format, the position may need adjusting.

---

## Uninstall

```bash
# Stop the automatic processing
launchctl unload ~/Library/LaunchAgents/com.notebooklm-scrubber.plist

# Delete the files
rm -rf ~/notebooklm-scrubber
rm ~/Library/LaunchAgents/com.notebooklm-scrubber.plist
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
├── watch-and-scrub.sh            # Folder watcher
├── install.sh                    # One-line installer
├── setup.sh                      # Local setup script
├── com.notebooklm-scrubber.plist.template
├── requirements.txt
└── README.md
```

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

---

## Related: PDF to Slides Conversion Research

Want to convert your NotebookLM PDFs into editable presentations? Check out the [`pdf-to-slides-research/`](./pdf-to-slides-research/) folder for:

- **What was tested:** Codia Visual Struct API, PyMuPDF + Gemini Vision, python-pptx
- **What worked:** Manual Codia browser conversion, individual components
- **What didn't work:** Full automation (OCR errors, positioning issues)
- **Python scripts:** Working extraction, vision analysis, and PPTX generation code

**TL;DR:** No fully automated solution worked reliably. Use [Codia AI NoteSlide](https://noteslide.codia.ai/) in the browser + manual review for best results.

---

## License

MIT - Use it however you want.
