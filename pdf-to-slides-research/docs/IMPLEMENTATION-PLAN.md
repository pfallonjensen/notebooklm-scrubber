# PDF-to-Google Slides Converter - Implementation Plan

**Project Location:** `/Users/youruser/Obsidian Vault/Automations/pdf-to-slides-converter/`

**Status:** Planning Complete - Ready for Implementation

**Estimated Effort:** 9-12 hours over 3 sessions

---

## Overview

Build a standalone automation that converts cleaned NotebookLM PDFs to editable Google Slides presentations with 85-90% fidelity using a hybrid extraction approach.

**Tech Stack:**
- **PyMuPDF (fitz)** - Extract images, text, and page data from PDF
- **Google Gemini Vision API** - Analyze page structure/hierarchy (FREE with Workspace)
- **Google Slides API** - Create editable slides directly (FREE with Workspace)

**Goal:** User drops PDF → auto-converts → saves 2-3 hours per deck

---

## Architecture

### File Structure
```
Automations/pdf-to-slides-converter/
├── docs/
│   ├── IMPLEMENTATION-PLAN.md    # This file - overall plan
│   ├── SESSION-NOTES.md          # Session-by-session progress tracking
│   ├── CONTEXT.md                # Important context across sessions
│   └── PREREQUISITES.md          # Setup instructions
├── src/
│   ├── convert-to-slides.py     # Main orchestration script
│   ├── pdf_processor.py         # PyMuPDF extraction
│   ├── vision_analyzer.py       # Gemini Vision analysis
│   ├── slide_builder.py         # Google Slides API
│   └── config.py                # Configuration management
├── credentials/                  # OAuth tokens (gitignored)
│   └── google-oauth-token.pickle
├── tests/                        # Test files and sample PDFs
├── venv/                         # Virtual environment
├── requirements.txt              # Dependencies
├── .env                          # Environment variables (gitignored)
├── .gitignore
├── README.md                     # User-facing documentation
└── convert.log                   # Processing log
```

### Processing Pipeline

```
PDF Input → Page Extraction → Vision Analysis → Slide Generation → Output

1. PDF Extraction (PyMuPDF):
   - Pages as PNG (150 DPI) → for Vision
   - Embedded images → original quality
   - Text blocks with bounding boxes → accurate text

2. Structure Analysis (Gemini Vision):
   - Send PNG to Gemini Vision → structure JSON
   - Merge Vision structure with PDF content
   - Result: Complete page data (content + layout + hierarchy)

3. Slide Creation (Google Slides API):
   - Create presentation in Google Slides
   - For each page: Add slide, add text boxes, add images
   - Batch update API calls for efficiency
   - Return: presentation_url

Output: Editable Google Slides in user's Drive
```

---

## Implementation Phases

### Phase 1: PDF Extraction & Vision Analysis (3-4 hours)

**Status:** Not Started

**Goals:**
- Extract pages, images, text from PDF
- Send to Gemini Vision, get structure JSON
- Validate responses

**Tasks:**
1. Set up project structure and virtual environment
2. Implement `pdf_processor.py`:
   - `extract_pages_as_images()` - Convert PDF pages to PNG
   - `extract_embedded_images()` - Get original images with positions
   - `extract_text_blocks()` - Get text with formatting and bounding boxes
3. Implement `vision_analyzer.py`:
   - Gemini API client initialization
   - Prompt engineering for structure analysis
   - `analyze_page_structure()` with retry logic
4. Test with sample PDFs

**Validation:**
```bash
python3 test_extraction.py "test.pdf"
# Should show: page images, Vision JSON, PDF text/images
```

### Phase 2: Slides API & Slide Building (4-5 hours)

**Status:** Not Started

**Goals:**
- Authenticate with Google Slides API
- Create presentations and slides
- Build slides from merged data

**Tasks:**
1. OAuth setup (one-time user setup)
2. Implement `slide_builder.py`:
   - OAuth token management
   - `create_presentation()` - Create new presentation
   - `add_text_box()` - Add text with positioning
   - `add_image()` - Upload to Drive and embed
   - `batch_update()` - Efficient API wrapper
3. Coordinate conversion (PDF points → Slides EMUs)
4. Build complete slides from merged data
5. End-to-end test

**Validation:**
```bash
python3 convert-to-slides.py "test.pdf"
# Should output: Presentation URL
# Open link → editable slides with ~85% fidelity
```

### Phase 3: Polish & Automation (2-3 hours)

**Status:** Not Started

**Goals:**
- Robust error handling
- Configuration management
- Watch-and-convert automation
- Documentation

**Tasks:**
1. Error handling (retries, fallbacks, logging)
2. Integrate AlertManager for error notifications
3. Create `watch-and-convert.sh` for automation
4. Create LaunchAgent plist for scheduled runs
5. Write README.md with setup instructions
6. Test full workflow

**Validation:**
```bash
cp test.pdf "$WATCH_DIR/"
# Wait 5 min → check logs → verify conversion → check Drive
```

---

## Key Implementation Details

### PyMuPDF Extraction (pdf_processor.py)

```python
class PDFProcessor:
    def extract_pages_as_images(pdf_path: str, dpi=150) -> List[PIL.Image]:
        """Convert pages to PNG for Gemini Vision (balance quality vs 4MB limit)"""

    def extract_embedded_images(pdf_path: str, page_num: int) -> List[Dict]:
        """Get original images with positions: [(bytes, bbox, index)]"""

    def extract_text_blocks(pdf_path: str, page_num: int) -> List[Dict]:
        """Get text with formatting: [(text, bbox, font_size, font_name)]"""
```

**Key Points:**
- Use `fitz.open()` (same library as existing scrubber)
- Page images: `page.get_pixmap(dpi=150)` → convert to PIL Image
- Image extraction: `doc.extract_image(xref)` for each xref
- Text: `page.get_text("dict")` gives block-level structure

### Gemini Vision Analysis (vision_analyzer.py)

```python
class VisionAnalyzer:
    def analyze_page_structure(page_image: PIL.Image, page_num: int) -> Dict:
        """
        Returns JSON:
        {
            "page_type": "title_slide" | "content_slide" | "section_header",
            "title": "Main title",
            "subtitle": "Subtitle if present",
            "content_blocks": [
                {
                    "type": "text" | "bullet_list" | "image" | "table",
                    "position": {"x": 0.1, "y": 0.3, "width": 0.8, "height": 0.5},
                    "hierarchy_level": 1,
                    "content": "Text or description"
                }
            ],
            "layout": "single_column" | "two_column" | "custom",
            "visual_hierarchy": ["title", "image", "bullets", "caption"]
        }
        """
```

**API Configuration:**
- Model: `gemini-1.5-flash` (free tier)
- Temperature: 0.1 (low for consistency)
- Response format: `application/json`
- Rate limit: 15 requests/minute (sequential processing)
- Retry: Exponential backoff on 429 errors

### Google Slides API (slide_builder.py)

```python
class SlideBuilder:
    def create_presentation(title: str) -> str:
        """Create presentation, returns presentation_id"""

    def add_text_box(presentation_id: str, slide_id: str,
                     text: str, position: Dict, style: Dict):
        """Add text box with positioning and styling"""

    def add_image(presentation_id: str, slide_id: str,
                  image_url: str, position: Dict):
        """Upload to Drive → embed in slide"""

    def batch_update(presentation_id: str, requests: List[Dict]):
        """Execute multiple updates in single API call (efficient)"""
```

**Coordinate Conversion:**
- PDF: Points (72 DPI), origin top-left
- Slides: EMUs (914400/inch), origin top-left
- Standard slide: 10" x 7.5" = 9144000 x 6858000 EMUs

### OAuth Authentication

**Approach:** OAuth 2.0 (user-owned files, not service account)

**One-time Setup (User runs):**
1. Enable APIs in Google Cloud Console (Slides, Drive, Generative Language)
2. Create OAuth Client ID → Desktop app
3. Download JSON → save as `credentials/client_secret.json`
4. First run: `python3 convert-to-slides.py --setup`
   - Opens browser → log in → grant permissions
   - Token saved to `credentials/google-oauth-token.pickle`
5. Subsequent runs: Automatic (token auto-refreshes)

---

## Error Handling & Robustness

### Rate Limits
- **Gemini Vision**: 15 RPM → Sequential processing (~1s/page)
- **Google Slides API**: 300 RPM → Batch updates (single call per slide)
- **Retry Strategy**: Exponential backoff (2s, 4s, 8s)

### Failed Conversions
1. **Corrupted PDF**: Log error, skip file
2. **Gemini Failure**: Retry 3x → fall back to text-only
3. **Slides API Failure**: Log error, save progress
4. **Partial Success**: Keep partial presentation, log missing pages

### Logging
- `convert.log` - Detailed conversion log
- `Automations/logs/pdf-to-slides-converter.log` - Central log
- Slack alerts via AlertManager for errors only

---

## Configuration (config.py)

```python
@dataclass
class Config:
    # Paths
    WATCH_DIR: Path = Path("/Users/youruser/My Drive (your.email@company.com)/Your-Watch-Folder")
    OUTPUT_DRIVE_FOLDER: str = "NotebookLM Slides"
    CREDENTIALS_DIR: Path = Path(__file__).parent / "credentials"

    # PyMuPDF
    PDF_DPI: int = 150  # Balance quality vs size
    MAX_IMAGE_SIZE_MB: int = 4  # Gemini limit

    # Gemini
    GEMINI_MODEL: str = "gemini-1.5-flash"
    GEMINI_TEMPERATURE: float = 0.1
    GEMINI_MAX_RETRIES: int = 3

    # Slides
    DEFAULT_FONT: str = "Arial"
    DEFAULT_FONT_SIZE: int = 18
    TITLE_FONT_SIZE: int = 36
```

**Environment Variables (.env):**
```bash
GOOGLE_GEMINI_API_KEY="your-key-here"  # From AI Studio
```

---

## Testing Strategy

### Test Cases
1. Basic Conversion: Simple 5-page deck
2. Complex Layouts: Multi-column, tables, charts
3. Large Deck: 50 pages (rate limiting test)
4. Text-Heavy: Long paragraphs, bullet lists
5. Image-Heavy: Large images, diagrams
6. Edge Cases: Empty slides, rotated pages, special characters

### Fidelity Validation (85-90% Target)

**Checklist:**
- ✅ **Content Accuracy (50%)**: All text present, images identifiable
- ✅ **Structure & Hierarchy (30%)**: Titles correct, points vs details distinguished
- ✅ **Layout & Positioning (20%)**: Elements in correct area, no major overlaps

**Acceptable Deviations:**
- Exact font matching (use standard fonts)
- Precise colors (approximate OK)
- Pixel-perfect positioning (general placement OK)

---

## Dependencies (requirements.txt)

```txt
# PDF Processing
PyMuPDF==1.24.0
Pillow==10.2.0

# Google APIs
google-generativeai==0.8.0
google-auth-oauthlib==1.2.0
google-auth-httplib2==0.2.0
google-api-python-client==2.130.0

# Utilities
requests==2.31.0
python-dotenv==1.0.0
```

---

## Success Criteria

- ✅ Phase 1: Extract PDF content + Gemini Vision returns valid JSON
- ✅ Phase 2: Create editable slides with 85-90% fidelity
- ✅ Phase 3: Error handling + automation complete
- ✅ Overall: User drops PDF → auto-converts → saves 2-3 hours per deck

---

## Reference Files

**Existing Automations for Patterns:**
- `/Users/youruser/Obsidian Vault/Automations/notebooklm-scrub/scrub-notebooklm-logo.py` - PyMuPDF usage patterns
- `/Users/youruser/Obsidian Vault/Automations/alert_manager.py` - Logging and notification patterns
- `/Users/youruser/Obsidian Vault/Automations/notebooklm-scrub/watch-and-scrub.sh` - Watch folder automation pattern

---

## Next Steps

1. **User completes prerequisites** (see PREREQUISITES.md)
2. **Implementation Session 1**: PDF extraction + Vision analysis
3. **Implementation Session 2**: Slides API + OAuth setup + conversion
4. **Implementation Session 3**: Error handling + automation + testing

**Track progress in:** `SESSION-NOTES.md`
