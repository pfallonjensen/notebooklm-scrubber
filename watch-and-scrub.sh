#!/bin/bash
# NotebookLM Logo Scrubber - Watch and Process Script
# Watches a folder for new PDFs and removes the NotebookLM watermark

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_DIR="$SCRIPT_DIR/venv"
LOG_FILE="$SCRIPT_DIR/scrub.log"
PROCESSED_FILE="$SCRIPT_DIR/.processed_files"

# ============================================================
# CONFIGURATION - Edit this path to your watch folder
# ============================================================
WATCH_DIR="${NOTEBOOKLM_WATCH_DIR:-$HOME/NotebookLM-PDFs}"
# ============================================================

# Ensure processed file exists
touch "$PROCESSED_FILE"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
}

# Wait for file to finish syncing (useful for cloud storage like Google Drive)
wait_for_file_ready() {
    local file="$1"
    local max_wait=30  # Max 30 seconds
    local waited=0

    while [ $waited -lt $max_wait ]; do
        # Get current file size
        local size1=$(stat -f%z "$file" 2>/dev/null || stat -c%s "$file" 2>/dev/null || echo "0")
        sleep 2
        local size2=$(stat -f%z "$file" 2>/dev/null || stat -c%s "$file" 2>/dev/null || echo "0")

        # If size is stable and non-zero, file is ready
        if [ "$size1" = "$size2" ] && [ "$size1" != "0" ]; then
            return 0
        fi

        waited=$((waited + 2))
        log "Waiting for file to sync: $(basename "$file") (${waited}s)"
    done

    return 1  # Timeout
}

log "=== Starting NotebookLM scrubber ==="
log "Watching: $WATCH_DIR"

# Check if watch directory exists
if [ ! -d "$WATCH_DIR" ]; then
    log "ERROR: Watch directory does not exist: $WATCH_DIR"
    echo "ERROR: Watch directory does not exist: $WATCH_DIR"
    echo "Set NOTEBOOKLM_WATCH_DIR environment variable or edit this script."
    exit 1
fi

# Activate virtual environment
source "$VENV_DIR/bin/activate"

# Find all PDF files in the watch directory
find "$WATCH_DIR" -maxdepth 1 -name "*.pdf" -type f | while read -r pdf_file; do
    # Skip if already a _clean file
    if [[ "$pdf_file" == *"_clean.pdf" ]]; then
        continue
    fi

    # Get the base name and clean file path
    base_name="${pdf_file%.pdf}"
    clean_file="${base_name}_clean.pdf"

    # Skip if clean version already exists
    if [ -f "$clean_file" ]; then
        continue
    fi

    # Skip if already processed (check by file path hash)
    file_hash=$(echo "$pdf_file" | shasum | cut -d' ' -f1)
    if grep -q "$file_hash" "$PROCESSED_FILE" 2>/dev/null; then
        continue
    fi

    log "Processing: $(basename "$pdf_file")"

    # Wait for file to finish syncing from cloud storage
    if ! wait_for_file_ready "$pdf_file"; then
        log "SKIP: File still syncing after timeout: $(basename "$pdf_file")"
        continue
    fi

    # Run the scrubber
    python3 "$SCRIPT_DIR/scrub-notebooklm-logo.py" "$pdf_file" "$clean_file" >> "$LOG_FILE" 2>&1

    if [ $? -eq 0 ]; then
        log "SUCCESS: Created $(basename "$clean_file")"
        echo "$file_hash" >> "$PROCESSED_FILE"
    else
        log "ERROR: Failed to process $(basename "$pdf_file")"
    fi
done

log "=== Scrubber run complete ==="
