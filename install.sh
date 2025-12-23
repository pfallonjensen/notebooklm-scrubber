#!/bin/bash
# =============================================================================
# NotebookLM Logo Scrubber - One-Click Installer
#
# Run this with:
#   curl -fsSL https://raw.githubusercontent.com/pfallonjensen/notebooklm-scrubber/main/install.sh | bash
#
# Or download and run:
#   chmod +x install.sh && ./install.sh
# =============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

echo ""
echo -e "${BOLD}========================================${NC}"
echo -e "${BOLD}  NotebookLM Logo Remover - Installer${NC}"
echo -e "${BOLD}========================================${NC}"
echo ""

# Check for required tools
check_requirements() {
    echo -e "${BLUE}Checking requirements...${NC}"

    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}Error: Python 3 is required but not installed.${NC}"
        echo ""
        echo "Please install Python 3 first:"
        echo "  - Mac: Download from https://www.python.org/downloads/"
        echo "  - Or install via Homebrew: brew install python3"
        exit 1
    fi

    if ! command -v curl &> /dev/null && ! command -v git &> /dev/null; then
        echo -e "${RED}Error: curl or git is required to download files.${NC}"
        exit 1
    fi

    echo -e "${GREEN}✓ All requirements met${NC}"
    echo ""
}

# Download the project
download_project() {
    INSTALL_DIR="$HOME/notebooklm-scrubber"

    echo -e "${BLUE}Downloading NotebookLM Scrubber...${NC}"

    if [ -d "$INSTALL_DIR" ]; then
        echo "Installation folder already exists at $INSTALL_DIR"
        read -p "Remove it and reinstall? (y/n) " -n 1 -r
        echo ""
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            rm -rf "$INSTALL_DIR"
        else
            echo "Keeping existing installation. Exiting."
            exit 0
        fi
    fi

    # Try git first, fall back to curl
    if command -v git &> /dev/null; then
        git clone --quiet https://github.com/pfallonjensen/notebooklm-scrubber.git "$INSTALL_DIR"
    else
        mkdir -p "$INSTALL_DIR"
        curl -fsSL https://github.com/pfallonjensen/notebooklm-scrubber/archive/main.tar.gz | tar -xz -C "$INSTALL_DIR" --strip-components=1
    fi

    echo -e "${GREEN}✓ Downloaded to $INSTALL_DIR${NC}"
    echo ""
}

# Get watch folder from user
get_watch_folder() {
    echo -e "${BOLD}Where do you want to drop your NotebookLM PDFs?${NC}"
    echo ""
    echo "This is the folder you'll use to process PDFs."
    echo "Drop a PDF in → get a clean PDF out (without the logo)."
    echo ""
    echo "Examples:"
    echo "  ~/Documents/NotebookLM"
    echo "  ~/Desktop/NotebookLM-PDFs"
    echo "  ~/Google Drive/NotebookLM"
    echo ""

    # Suggest a default
    DEFAULT_WATCH="$HOME/Documents/NotebookLM-PDFs"

    read -p "Folder path (press Enter for $DEFAULT_WATCH): " WATCH_DIR

    # Use default if empty
    if [ -z "$WATCH_DIR" ]; then
        WATCH_DIR="$DEFAULT_WATCH"
    fi

    # Expand ~
    WATCH_DIR="${WATCH_DIR/#\~/$HOME}"

    # Create if doesn't exist
    if [ ! -d "$WATCH_DIR" ]; then
        echo ""
        read -p "This folder doesn't exist. Create it? (y/n) " -n 1 -r
        echo ""
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            mkdir -p "$WATCH_DIR"
            echo -e "${GREEN}✓ Created folder${NC}"
        else
            echo -e "${RED}Please create the folder first and run this installer again.${NC}"
            exit 1
        fi
    fi

    echo ""
    echo -e "${GREEN}✓ Watch folder: $WATCH_DIR${NC}"
    echo ""
}

# Set up Python environment
setup_python() {
    echo -e "${BLUE}Setting up Python environment...${NC}"

    cd "$INSTALL_DIR"

    # Create virtual environment
    python3 -m venv venv

    # Install dependencies
    source venv/bin/activate
    pip install --quiet --upgrade pip
    pip install --quiet pymupdf pillow

    echo -e "${GREEN}✓ Python packages installed${NC}"
    echo ""
}

# Set up automation (macOS LaunchAgent)
setup_automation() {
    echo -e "${BLUE}Setting up automatic processing...${NC}"

    # Make scripts executable
    chmod +x "$INSTALL_DIR/scrub-notebooklm-logo.py"
    chmod +x "$INSTALL_DIR/watch-and-scrub.sh"

    # macOS only
    if [[ "$OSTYPE" == "darwin"* ]]; then
        PLIST_DIR="$HOME/Library/LaunchAgents"
        PLIST_FILE="$PLIST_DIR/com.notebooklm-scrubber.plist"

        mkdir -p "$PLIST_DIR"

        # Generate plist from template
        sed -e "s|{{INSTALL_DIR}}|$INSTALL_DIR|g" \
            -e "s|{{WATCH_DIR}}|$WATCH_DIR|g" \
            "$INSTALL_DIR/com.notebooklm-scrubber.plist.template" > "$PLIST_FILE"

        # Load the agent
        launchctl unload "$PLIST_FILE" 2>/dev/null || true
        launchctl load "$PLIST_FILE"

        echo -e "${GREEN}✓ Automatic processing enabled${NC}"
    else
        echo "Note: Automatic folder watching is only available on macOS."
        echo "You can still run the script manually on any system."
    fi
    echo ""
}

# Print success message
print_success() {
    echo -e "${BOLD}========================================${NC}"
    echo -e "${GREEN}${BOLD}  Installation Complete! 🎉${NC}"
    echo -e "${BOLD}========================================${NC}"
    echo ""
    echo -e "${BOLD}How to use:${NC}"
    echo ""
    echo "  1. Export a PDF from NotebookLM"
    echo "  2. Drop it in: $WATCH_DIR"
    echo "  3. A clean version appears automatically!"
    echo "     (filename_clean.pdf - without the logo)"
    echo ""
    echo -e "${BOLD}That's it!${NC} The logo is removed automatically."
    echo ""
    echo "---"
    echo ""
    echo "Manual usage (for single files):"
    echo "  $INSTALL_DIR/venv/bin/python3 $INSTALL_DIR/scrub-notebooklm-logo.py yourfile.pdf"
    echo ""
    echo "Logs (if something goes wrong):"
    echo "  $INSTALL_DIR/scrub.log"
    echo ""
}

# Main installation flow
main() {
    check_requirements
    download_project
    get_watch_folder
    setup_python
    setup_automation
    print_success
}

main
