#!/usr/bin/env python3
"""
Configuration management for PDF to Slides Converter
Centralizes all settings, paths, and API configuration
"""

import os
from dataclasses import dataclass
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv(Path(__file__).parent.parent / ".env")


@dataclass
class Config:
    """Central configuration for PDF to Slides Converter"""

    # === Paths ===
    PROJECT_ROOT: Path = Path(__file__).parent.parent
    WATCH_DIR: Path = Path("/Users/youruser/My Drive (your.email@company.com)/Your-Watch-Folder")
    OUTPUT_DRIVE_FOLDER: str = "NotebookLM Slides"
    LOG_FILE: Path = PROJECT_ROOT / "convert.log"

    # === Shared OAuth Credentials (claude-mcp-integration project) ===
    # Uses the same Google Cloud project as Google Workspace MCP
    MCP_CONFIG_DIR: Path = Path.home() / ".config" / "google-workspace-mcp"
    CREDENTIALS_DIR: Path = MCP_CONFIG_DIR  # Point to shared location

    # === PyMuPDF Settings ===
    PDF_DPI: int = 150  # Balance quality vs size (Gemini has 4MB limit)
    MAX_IMAGE_SIZE_MB: int = 4  # Gemini Vision limit

    # === Gemini Vision API ===
    GEMINI_MODEL: str = "gemini-2.5-flash"  # Free tier model with excellent vision support
    GEMINI_TEMPERATURE: float = 0.1  # Low for consistency
    GEMINI_MAX_RETRIES: int = 3  # Retry attempts for rate limits
    GEMINI_RETRY_DELAY: int = 2  # Seconds between retries

    # === Google Slides API ===
    DEFAULT_FONT: str = "Arial"
    DEFAULT_FONT_SIZE: int = 18
    TITLE_FONT_SIZE: int = 36
    SUBTITLE_FONT_SIZE: int = 24

    # === Slide Dimensions (EMUs) ===
    # Standard slide: 10" x 7.5" = 9144000 x 6858000 EMUs
    # EMU (English Metric Unit) = 914400 per inch
    SLIDE_WIDTH_EMU: int = 9144000
    SLIDE_HEIGHT_EMU: int = 6858000

    # === API Keys & Credentials ===
    @property
    def GEMINI_API_KEY(self) -> str:
        """Get Gemini API key from environment"""
        key = os.getenv("GOOGLE_GEMINI_API_KEY")
        if not key:
            raise ValueError(
                "GOOGLE_GEMINI_API_KEY not set in .env file. "
                "Get your key from: https://aistudio.google.com/apikey"
            )
        return key

    @property
    def CLIENT_SECRET_PATH(self) -> Path:
        """Path to OAuth client secret JSON (shared with Google Workspace MCP)"""
        path = self.MCP_CONFIG_DIR / "your-oauth-credentials.json"
        if not path.exists():
            raise FileNotFoundError(
                f"OAuth credentials not found at {path}. "
                "Run the Google Workspace MCP setup first."
            )
        return path

    @property
    def OAUTH_TOKEN_PATH(self) -> Path:
        """Path to OAuth token pickle file (in shared MCP config dir)"""
        return self.MCP_CONFIG_DIR / "pdf-to-slides-token.pickle"

    # === OAuth Scopes ===
    OAUTH_SCOPES = [
        'https://www.googleapis.com/auth/presentations',  # Google Slides
        'https://www.googleapis.com/auth/drive.file',      # Google Drive (files created by app)
    ]

    # === Logging ===
    LOG_FORMAT: str = "[%(asctime)s] %(levelname)s: %(message)s"
    LOG_DATE_FORMAT: str = "%Y-%m-%d %H:%M:%S"

    def __post_init__(self):
        """Ensure required directories exist"""
        # Note: MCP_CONFIG_DIR should already exist from Google Workspace MCP setup
        self.PROJECT_ROOT.mkdir(parents=True, exist_ok=True)


# Global config instance
config = Config()


def validate_config() -> list[str]:
    """
    Validate configuration and return list of issues
    Returns empty list if all OK
    """
    issues = []

    # Check API key
    try:
        _ = config.GEMINI_API_KEY
    except ValueError as e:
        issues.append(str(e))

    # Check OAuth credentials (shared with Google Workspace MCP)
    try:
        _ = config.CLIENT_SECRET_PATH
    except FileNotFoundError as e:
        issues.append(str(e))

    # Check MCP config directory exists
    if not config.MCP_CONFIG_DIR.exists():
        issues.append(
            f"Google Workspace MCP config not found at {config.MCP_CONFIG_DIR}. "
            "Please set up Google Workspace MCP first."
        )

    # Check watch directory exists
    if not config.WATCH_DIR.exists():
        issues.append(f"Watch directory does not exist: {config.WATCH_DIR}")

    return issues


if __name__ == "__main__":
    """Test configuration"""
    print("=== PDF to Slides Converter - Configuration ===\n")

    print(f"Project Root: {config.PROJECT_ROOT}")
    print(f"Watch Directory: {config.WATCH_DIR}")
    print(f"Credentials Directory: {config.CREDENTIALS_DIR}")
    print(f"Log File: {config.LOG_FILE}\n")

    print(f"Gemini Model: {config.GEMINI_MODEL}")
    print(f"PDF DPI: {config.PDF_DPI}")
    print(f"Slide Dimensions: {config.SLIDE_WIDTH_EMU} x {config.SLIDE_HEIGHT_EMU} EMUs\n")

    print("Validating configuration...")
    issues = validate_config()
    if issues:
        print("\n❌ Configuration Issues:")
        for issue in issues:
            print(f"  - {issue}")
    else:
        print("✅ Configuration valid!")
        print(f"\nGemini API Key: {config.GEMINI_API_KEY[:20]}...")
        print(f"OAuth Credentials: {config.CLIENT_SECRET_PATH.name}")
