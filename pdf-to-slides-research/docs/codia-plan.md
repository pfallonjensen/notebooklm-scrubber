# Codia JSON → PPTX Converter Plan

## Overview
Build a converter that takes Codia Visual Struct JSON and produces high-fidelity PowerPoint files, with OCR error correction.

---

## Part 1: OCR Error Correction

### Observed Errors in Codia Output
- "supplyyote" → "supply chain" (character substitution + truncation)
- "inteligent" → "intelligent" (missing letter)
- "i\nS" misread from icon/graphic
- Line breaks in wrong places

### Correction Strategy: Two-Stage Pipeline

**Stage 1: Regex Pre-Filter (fast, free)**
```python
KNOWN_FIXES = {
    r'supplyyote': 'supply chain',
    r'inteligent': 'intelligent',
    r'\bi\nS\b': '',  # Remove misread icons
    r'ROl': 'ROI',    # Common l/I confusion
}
```
Catches ~80% of errors instantly, reduces API calls.

**Stage 2: Claude Sonnet 4 (quality)**
```python
def fix_ocr_text(text: str, slide_context: str = "") -> str:
    """Use Sonnet 4 for context-aware OCR correction."""
    prompt = f"""Fix OCR errors in this slide text. Only fix obvious mistakes.
    Preserve all formatting and line breaks. Return ONLY the corrected text.

    Slide title: {slide_context}
    Text: {text}"""
    # Sonnet 4: ~$0.003/call, 99.5% accuracy, 1-2s
```

**Why Sonnet over Opus:**
- OCR correction is pattern-matching, not deep reasoning
- Opus ($0.015/call) is 5x cost for marginal quality gain
- Sonnet handles business terminology equally well for this task

**Batching Strategy:**
- Collect all text blocks from a slide
- Single API call per slide (not per text block)
- ~10 slides = ~$0.03 total API cost

---

## Part 2: Converter Architecture

### Input: Codia JSON Structure
```
visual_struct.visualElement.childElements[] → recursive tree
Each element has:
- elementType: Text | Image | Layer | Body
- contentData.textValue or contentData.imageSource
- layoutConfig.absoluteAttrs.coord [x, y]
- styleConfig: dimensions, colors, fonts
```

### Output: PPTX via python-pptx

### Key Conversions

| Codia (px) | PPTX (EMU) | Formula |
|------------|------------|---------|
| baseWidth: 2867 | 9144000 | `emu = px * (9144000 / 2867)` |
| height: 1600 | 6858000 | `emu = px * (6858000 / 1600)` |

### Module: `src/codia_to_pptx.py`

```python
class CodiaConverter:
    def __init__(self, codia_json: dict):
        self.data = codia_json
        self.config = codia_json['visual_struct']['configuration']
        self.scale_x = Inches(10) / self.config['baseWidth']
        self.scale_y = Inches(7.5) / 1600  # standard height

    def convert(self, output_path: str) -> str:
        prs = Presentation()
        prs.slide_width = Inches(10)
        prs.slide_height = Inches(7.5)

        slide = prs.slides.add_slide(prs.slide_layouts[6])  # blank
        root = self.data['visual_struct']['visualElement']
        self._process_element(slide, root)

        prs.save(output_path)
        return output_path

    def _process_element(self, slide, element, parent_offset=(0,0)):
        """Recursively process element tree."""
        etype = element.get('elementType')

        if etype == 'Text':
            self._add_text(slide, element, parent_offset)
        elif etype == 'Image':
            self._add_image(slide, element, parent_offset)
        elif etype in ('Layer', 'Body'):
            # Process children with offset accumulation
            for child in element.get('childElements', []):
                self._process_element(slide, child, parent_offset)
```

---

## Part 3: Gotchas & Solutions

### 1. Coordinate Origin Mismatch
**Problem:** Codia uses `orginCoord` (original) vs `coord` (adjusted)
**Solution:** Use `orginCoord` for absolute positioning, ignore `coord`

### 2. Font Mapping
**Problem:** Codia detects fonts like "Rethink Sans" not in PPTX
**Solution:** Map to safe fallbacks:
```python
FONT_MAP = {
    'Rethink Sans': 'Arial',
    'Inter': 'Arial',
    'Manrope': 'Arial',
    'DM Sans': 'Arial',
    # Add more as discovered
}
```

### 3. Image Downloads
**Problem:** Images are S3 URLs that may expire
**Solution:** Download immediately, embed as bytes:
```python
def _add_image(self, slide, element, offset):
    url = element['contentData']['imageSource']
    if url:
        response = requests.get(url, timeout=30)
        img_stream = io.BytesIO(response.content)
        # Add to slide from stream
```

### 4. Text Color Format
**Problem:** Codia gives RGB as `[r, g, b]` array
**Solution:** Convert to python-pptx RGBColor:
```python
rgb = element['styleConfig']['textColor']['rgbValues']
run.font.color.rgb = RGBColor(rgb[0], rgb[1], rgb[2])
```

### 5. Nested Groups/Layers
**Problem:** Elements nested in "Layer" groups with relative coords
**Solution:** Accumulate offsets through recursion (already in architecture)

### 6. Z-Order (Layering)
**Problem:** Images should be behind text
**Solution:** Process in order: Background → Images → Text (Codia already orders this way)

### 7. Text Box Sizing
**Problem:** Codia gives exact dimensions but PPTX auto-sizes
**Solution:** Set explicit width/height, disable auto-fit:
```python
tf.word_wrap = True
tf.auto_size = MSO_AUTO_SIZE.NONE
```

### 8. Multi-line Text
**Problem:** Codia may split text across elements or embed \n
**Solution:** Preserve \n, let PPTX handle wrapping within box

---

## Part 4: File Structure

```
src/
├── codia_to_pptx.py      # NEW: Main converter
├── ocr_corrector.py      # NEW: LLM-based text fixer
├── config.py             # Existing: Add PPTX settings
└── ...existing files...

tests/
├── codia_test_page0.json # Save test JSON
├── codia_test_page5.json
└── codia_test_page9.json
```

---

## Part 5: Decisions Made

| Question | Decision |
|----------|----------|
| Input source | NotebookLM exports only |
| Output format | PPTX (local file, can upload to Slides later) |
| OCR model | Sonnet 4 with regex pre-filter |
| Quality vs speed | Quality prioritized |

### Remaining Productization Questions

**For Future Iteration:**
1. **Scale**: How many decks/week? (affects caching strategy)
2. **Error UX**: Show OCR confidence scores? Allow manual edits?
3. **Automation**: Watch folder for new PDFs? Webhook on completion?
4. **Fallback**: If Codia fails, use image-only slides or abort?

---

## Implementation Order

1. **Save test JSON** - Capture the 3 successful Codia outputs
2. **Build basic converter** - Codia JSON → PPTX (no OCR fix)
3. **Test with sample data** - Verify positioning, fonts, colors
4. **Add OCR correction** - Integrate Claude Haiku post-processing
5. **Add image handling** - Download S3 images, embed in PPTX
6. **End-to-end test** - Full pipeline: PDF → Codia → Fix → PPTX

---

## Dependencies to Add

```
# Already in requirements.txt:
python-pptx>=0.6.21

# May need:
anthropic  # For Claude Haiku OCR correction
```

---

## Success Metrics

- **Fidelity:** Text position within 5% of original
- **OCR Accuracy:** <2% error rate after correction
- **Speed:** <60s for 10-page deck
- **Reliability:** >95% success rate on NotebookLM PDFs
