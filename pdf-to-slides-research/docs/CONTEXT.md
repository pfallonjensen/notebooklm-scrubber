# Project Context - PDF to Slides Converter

**Last Updated:** 2026-01-05

This file contains important context that should be preserved across multiple Claude Code sessions.

---

## Project Overview

**Goal:** Automatically convert NotebookLM PDF slide decks to editable Google Slides presentations

**User:** Fallon Jensen (VP Product, non-technical)

**Use Case:** NotebookLM generates client presentation PDFs (v1) → Convert to Google Slides → Customize for clients

**Requirements:**
- Must be reliable and maintainable
- 85-90% fidelity (content + structure accurate, styling approximate)
- Minimal manual cleanup needed
- Separate from existing watermark scrubber (don't break what works)

---

## Technical Context

### Existing System

**NotebookLM Watermark Scrubber:**
- Location: `/Users/youruser/Obsidian Vault/Automations/notebooklm-scrub/`
- Script: `scrub-notebooklm-logo.py` - Removes NotebookLM logo from PDFs
- Automation: `watch-and-scrub.sh` - Watches folder, auto-processes
- Uses: PyMuPDF (fitz), has working virtual environment
- Status: Working perfectly - DO NOT MODIFY

**Watch Folder:**
- `/Users/youruser/My Drive (your.email@company.com)/Your-Watch-Folder`
- Mirrored Google Drive folder (instant sync)

### Why Hybrid Approach?

**Challenges with PDF extraction only:**
- PDFs don't preserve semantic structure (titles, bullets, hierarchy)
- Text positioning unreliable
- Layout detection difficult

**Challenges with Vision only:**
- Can't extract exact fonts/colors
- Text OCR less accurate than PDF text
- Image extraction approximate

**Hybrid solution:**
- Vision API → understands structure, layout, hierarchy
- PDF extraction → accurate text, original images
- Combine → best of both worlds
- Result: 85-90% fidelity achievable in reasonable development time

### Why Not Higher Fidelity?

**90-95% would require:**
- Font extraction and matching (many PDFs use fonts not in Google Slides)
- Precise color extraction for every element
- Pixel-perfect positioning algorithms
- 2-3x more development time (~100-150 hours vs 40-60 hours)

**Decision:** 85-90% sufficient for use case (user customizes anyway)

---

## API & Service Context

### Google Workspace Access

**User has:**
- Google Workspace subscription (includes Gemini)
- Access to Google Slides API (free)
- Access to Google Drive API (free)
- Access to Gemini Vision API (free tier: 15 RPM, 1500/day)

**Model Selection:**
- Using: `gemini-2.5-flash` (free tier, 1500 requests/day)
- Tested and working with excellent vision analysis
- Advanced models (Nano Banana Pro, Gemini 3) require billing (limit: 0 on free tier)
- Can upgrade later if needed, but gemini-2.5-flash performs well

**Rate Limits:**
- Gemini Vision: 15 requests/minute → ~1 second per page
- Google Slides API: 300 requests/minute → no practical limit
- Strategy: Sequential processing for Gemini, batch updates for Slides

### Authentication Strategy

**OAuth 2.0 (NOT service account):**
- Why: Service account files aren't accessible to user
- OAuth: User owns the files, can access in their Drive
- Setup: One-time browser authorization (~15 minutes)
- Maintenance: Token auto-refreshes, no intervention needed

---

## Design Decisions

### Architecture Choices

**Separate automation:**
- Don't modify working watermark scrubber
- Follows same patterns (watch folder, logging, LaunchAgent)
- Can run independently or in sequence

**Component structure:**
- `pdf_processor.py` - PDF extraction (PyMuPDF patterns from scrubber)
- `vision_analyzer.py` - Gemini Vision API calls
- `slide_builder.py` - Google Slides API
- `convert-to-slides.py` - Main orchestration
- `config.py` - Centralized configuration

**Error handling:**
- Retry with exponential backoff (rate limits)
- Fallback to text-only if Vision fails
- Partial success handling (keep what works)
- AlertManager integration (existing pattern)

### Data Flow

```
1. Input: cleaned_deck.pdf (from watermark scrubber)
2. Extract: Pages as PNG (Vision), embedded images (quality), text blocks (accuracy)
3. Analyze: Send PNG to Gemini → get structure JSON
4. Merge: Vision structure + PDF content → complete page data
5. Build: Create Google Slides presentation via API
6. Output: Presentation URL + link in Drive
```

### Coordinate Systems

**PDF:**
- Units: Points (72 DPI)
- Origin: Top-left
- Y-axis: Down

**Google Slides:**
- Units: EMUs (914400 per inch)
- Origin: Top-left
- Y-axis: Down
- Standard slide: 10" x 7.5" = 9144000 x 6858000 EMUs

**Conversion formula:**
```python
x_emu = (x_pdf / pdf_width) * SLIDE_WIDTH
y_emu = (y_pdf / pdf_height) * SLIDE_HEIGHT
```

---

## User Preferences & Constraints

**User is non-technical:**
- Needs clear documentation
- One-time setup should be guided step-by-step
- Automation should "just work" after setup
- Errors should be human-readable

**Workflow:**
1. NotebookLM generates PDF
2. Drops in Google Drive folder
3. Automation converts to Slides
4. User customizes in Google Slides
5. Presents to client

**Time savings:**
- Manual conversion: 2-3 hours per deck
- Automated: ~5 minutes
- User value: High

---

## Known Limitations

### What Won't Be Perfect

**Fonts:**
- PDFs may use custom/proprietary fonts
- Google Slides has limited font library
- Solution: Use similar standard fonts (Arial, etc.)

**Colors:**
- Exact color matching difficult
- Solution: Approximate (good enough for editing)

**Spacing/Positioning:**
- Pixel-perfect layout hard to achieve
- Solution: General positioning (user adjusts)

**Complex Elements:**
- Tables, charts, diagrams may not preserve perfectly
- Solution: Best-effort reconstruction, user can fix

### Acceptable Trade-offs

- Content accuracy: HIGH (all text, all images)
- Structure fidelity: HIGH (correct hierarchy, layout)
- Visual polish: MEDIUM (approximate styling)
- User expects to customize anyway, so not pixel-perfect is OK

---

## Testing Philosophy

### Success Criteria

**Phase 1:** Can extract PDF and get Vision JSON ✓
**Phase 2:** Can create editable slides ✓
**Phase 3:** Automated workflow works ✓

**Fidelity checklist:**
- [ ] All text present and readable (no omissions)
- [ ] Images present and positioned reasonably
- [ ] Titles identified correctly
- [ ] Bullet points vs body text distinguished
- [ ] Multi-column layouts approximated
- [ ] No major overlaps or missing content

**Real-world test:**
- User runs on actual NotebookLM deck
- Measures time to customize vs manual creation
- Feedback: "Good enough" or "needs improvement"

---

## Future Enhancements (Not Now)

**Possible future improvements:**
- Custom slide templates (branding)
- Style preservation rules (company colors, fonts)
- Batch processing multiple PDFs
- Quality metrics dashboard
- ML model fine-tuning for specific deck types

**Current scope:** Get basic automation working reliably

---

## Important Reminders

1. **Don't break the scrubber** - It works, keep it separate
2. **Free tier limits** - Design for 15 RPM, graceful degradation
3. **User will customize** - Don't over-optimize styling
4. **Document everything** - User needs to understand and maintain
5. **Store context here** - Future sessions need this info

---

## Resources & References

**Existing automations to reference:**
- NotebookLM scrubber: PyMuPDF patterns
- AlertManager: Logging and notifications
- Other LaunchAgents: Scheduling patterns

**External tools discovered:**
- Codia AI NoteSlide (commercial vision-based converter)
- Various PDF-to-Slides converters (mostly low quality)

**API Documentation:**
- Gemini Vision: https://ai.google.dev/gemini-api/docs/vision
- Google Slides: https://developers.google.com/slides/api
- PyMuPDF: https://pymupdf.readthedocs.io/
