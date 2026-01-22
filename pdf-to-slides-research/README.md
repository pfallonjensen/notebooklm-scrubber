# PDF to Slides/PowerPoint Conversion - Research & Implementation

This package documents several approaches attempted to convert PDF slide decks to editable presentation formats (Google Slides or PowerPoint).

**TL;DR:** No fully automated solution worked reliably. Manual Codia browser conversion + human review is currently the most reliable path.

---

## Executive Summary

### Approaches Attempted

| Approach | Implementation Status | Outcome |
|----------|----------------------|---------|
| **Codia Browser (manual)** | N/A (manual process) | **Works well** - Converts PDFs reliably when used interactively in browser |
| **Codia Visual Struct API** | Fully implemented | **Poor results** - OCR errors, positioning issues, inconsistent output |
| **Hybrid (PyMuPDF + Gemini Vision + Google Slides API)** | Partially implemented | **Phase 1 works** (extraction + analysis), Phase 2 never completed |

### Bottom Line

- **For immediate needs:** Use [Codia AI NoteSlide](https://noteslide.codia.ai/) in the browser, then manually fix any issues
- **For programmatic conversion:** The `codia_to_pptx.py` script converts Codia's JSON output to PPTX, but quality depends on Codia API output quality
- **Full automation:** Not achieved - requires more investment in OCR correction and positioning logic

---

## Libraries & APIs Tested

| Library/API | Purpose | Status | Notes |
|-------------|---------|--------|-------|
| `PyMuPDF (fitz)` | PDF extraction | Working | Excellent for extracting images, text blocks, metadata |
| `Gemini Vision API` | Structure analysis | Working | Accurately identifies slide structure and hierarchy |
| `python-pptx` | PPTX generation | Working | Reliable PowerPoint file creation |
| `Codia Visual Struct API` | PDF structure extraction | **Poor** | OCR errors, positioning issues |
| `Google Slides API` | Slide creation | Not tested | Phase 2 was never implemented |
| `anthropic` (Claude) | OCR error correction | Working | Two-stage pipeline (regex + LLM) |

### Why Codia Visual Struct API Didn't Work Well

The Visual Struct API returns structured JSON with text positions and styling, but:

1. **OCR Errors:** Frequent character substitutions (e.g., "supplyyote" instead of "supply chain")
2. **Positioning Issues:** Element coordinates were inconsistent across pages
3. **Missing Elements:** Some visual elements weren't detected
4. **Font Detection:** Fonts not available in PPTX required mapping to fallbacks

The browser-based Codia interface handles these issues better with human review, but the API alone wasn't reliable enough for automation.

---

## What's in This Package

### Source Code (`src/`)

| File | Lines | Purpose |
|------|-------|---------|
| `pdf_processor.py` | 240 | PyMuPDF-based PDF extraction (pages as images, embedded images, text blocks) |
| `vision_analyzer.py` | 195 | Gemini Vision API integration for structure analysis |
| `config.py` | 157 | Centralized configuration management |
| `codia_to_pptx.py` | 403 | Codia JSON to PPTX converter (high-fidelity positioning) |
| `ocr_corrector.py` | 275 | Two-stage OCR correction (regex + Claude Sonnet) |

### Documentation (`docs/`)

| File | Purpose |
|------|---------|
| `CONTEXT.md` | Project context, design decisions, trade-offs |
| `SESSION-NOTES.md` | Session-by-session progress and learnings |
| `IMPLEMENTATION-PLAN.md` | Detailed 3-phase implementation plan |
| `codia-plan.md` | Codia converter architecture and gotchas |

---

## Architecture Overview

### Approach 1: Hybrid (PyMuPDF + Gemini Vision + Google Slides)

```
PDF Input
    │
    ├─► PyMuPDF extracts: Pages as PNG, embedded images, text blocks
    │
    ├─► Gemini Vision analyzes: Layout, hierarchy, structure (JSON)
    │
    ├─► Merge: Vision structure + PDF content
    │
    └─► Google Slides API creates: Editable presentation
```

**Status:** Phase 1 (extraction + vision) working. Phase 2 (Slides API integration) never built.

### Approach 2: Codia Visual Struct API

```
PDF Input
    │
    └─► Upload to Codia Visual Struct API
            │
            └─► Returns structured JSON with:
                  - Element positions (x, y, width, height)
                  - Text content
                  - Font/styling info
                  - Image URLs (S3)
                      │
                      ├─► OCR Correction (regex + LLM)
                      │
                      └─► python-pptx generates: PPTX file
```

**Status:** Implemented (`codia_to_pptx.py`) but output quality depends on Codia API accuracy.

---

## Key Learnings

### What Worked

1. **PyMuPDF extraction** - Reliably extracts all content from PDFs
2. **Gemini Vision analysis** - Accurately identifies slide structure
3. **python-pptx generation** - Solid library for creating PPTX files
4. **Two-stage OCR correction** - Regex catches 80% of errors, LLM handles the rest

### What Didn't Work

1. **Codia Visual Struct API alone** - Too many OCR/positioning errors for automation
2. **Direct PDF → Slides conversion** - PDF structure doesn't preserve semantic meaning
3. **Full automation without human review** - Quality floor too low for client-facing work

### Recommendations for Future Attempts

- **Immediate:** Use Codia browser + manual review
- **Medium-term:** Invest in better OCR correction and positioning algorithms
- **Long-term:** Consider:
  - Adobe PDF Services API (not tested)
  - iLovePDF API (not tested)
  - Training a custom model on your specific PDF formats

---

## Setup Instructions (Reference)

### Dependencies

```bash
pip install pymupdf pillow python-pptx google-generativeai python-dotenv requests anthropic
```

### Environment Variables

```bash
# .env file
GOOGLE_GEMINI_API_KEY="your-gemini-api-key"  # From https://aistudio.google.com/apikey
ANTHROPIC_API_KEY="your-anthropic-key"       # Optional, for LLM OCR correction
```

### Usage Examples

```bash
# Test PDF extraction
python src/pdf_processor.py path/to/deck.pdf

# Test Vision analysis (requires Gemini API key)
python src/vision_analyzer.py path/to/slide.png

# Convert Codia JSON to PPTX
python src/codia_to_pptx.py input.json output.pptx

# Multi-page conversion
python src/codia_to_pptx.py --multi output.pptx page1.json page2.json page3.json
```

---

## File Inventory

```
pdf-to-slides-package/
├── README.md                    # This file
├── src/
│   ├── pdf_processor.py        # PyMuPDF extraction
│   ├── vision_analyzer.py      # Gemini Vision analysis
│   ├── config.py               # Configuration management
│   ├── codia_to_pptx.py        # Codia JSON → PPTX
│   └── ocr_corrector.py        # OCR error correction
└── docs/
    ├── CONTEXT.md              # Project context
    ├── SESSION-NOTES.md        # Progress notes
    ├── IMPLEMENTATION-PLAN.md  # Implementation plan
    └── codia-plan.md           # Codia converter plan
```

---

## License

Private research - use at your own discretion.

---

*Generated from Claude Code session, January 2026*
