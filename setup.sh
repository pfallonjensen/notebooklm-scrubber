#!/bin/bash
# NotebookLM Logo Scrubber - Setup Script
# Run this script to set up the automated PDF scrubber

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "============================================"
echo "  NotebookLM Logo Scrubber - Setup"
echo "============================================"
echo ""

# Get watch directory from user
if [ -z "$1" ]; then
    echo "Enter the folder path to watch for NotebookLM PDFs:"
    echo "(This is where you'll drop PDFs exported from NotebookLM)"
    echo ""
    read -p "> " WATCH_DIR
else
    WATCH_DIR="$1"
fi

# Expand ~ if present
WATCH_DIR="${WATCH_DIR/#\~/$HOME}"

# Validate watch directory
if [ ! -d "$WATCH_DIR" ]; then
    echo ""
    read -p "Directory doesn't exist. Create it? (y/n) " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        mkdir -p "$WATCH_DIR"
        echo "Created: $WATCH_DIR"
    else
        echo "Aborted. Please create the directory first."
        exit 1
    fi
fi

echo ""
echo "Watch directory: $WATCH_DIR"
echo "Install directory: $SCRIPT_DIR"
echo ""

# Step 1: Create virtual environment
echo "[1/4] Creating Python virtual environment..."
if [ ! -d "$SCRIPT_DIR/venv" ]; then
    python3 -m venv "$SCRIPT_DIR/venv"
    echo "      Created venv"
else
    echo "      venv already exists"
fi

# Step 2: Install dependencies
echo "[2/4] Installing Python dependencies..."
source "$SCRIPT_DIR/venv/bin/activate"
pip install --quiet --upgrade pip
pip install --quiet pymupdf pillow
echo "      Installed pymupdf, pillow"

# Step 3: Make scripts executable
echo "[3/4] Setting permissions..."
chmod +x "$SCRIPT_DIR/scrub-notebooklm-logo.py"
chmod +x "$SCRIPT_DIR/watch-and-scrub.sh"
echo "      Scripts are executable"

# Step 4: Create LaunchAgent (macOS only)
echo "[4/4] Setting up LaunchAgent..."
if [[ "$OSTYPE" == "darwin"* ]]; then
    PLIST_DIR="$HOME/Library/LaunchAgents"
    PLIST_FILE="$PLIST_DIR/com.notebooklm-scrubber.plist"

    mkdir -p "$PLIST_DIR"

    # Generate plist from template
    sed -e "s|{{INSTALL_DIR}}|$SCRIPT_DIR|g" \
        -e "s|{{WATCH_DIR}}|$WATCH_DIR|g" \
        "$SCRIPT_DIR/com.notebooklm-scrubber.plist.template" > "$PLIST_FILE"

    # Unload if already loaded
    launchctl unload "$PLIST_FILE" 2>/dev/null || true

    # Load the agent
    launchctl load "$PLIST_FILE"

    echo "      LaunchAgent installed and started"
else
    echo "      Skipped (not macOS)"
    echo "      For Linux, set up a cron job or systemd service manually."
fi

echo ""
echo "============================================"
echo "  Setup Complete!"
echo "============================================"
echo ""
echo "How it works:"
echo "  1. Drop a NotebookLM PDF into: $WATCH_DIR"
echo "  2. A cleaned version (*_clean.pdf) appears automatically"
echo ""
echo "Manual usage:"
echo "  python3 $SCRIPT_DIR/scrub-notebooklm-logo.py input.pdf [output.pdf]"
echo ""
echo "Logs:"
echo "  $SCRIPT_DIR/scrub.log"
echo ""
