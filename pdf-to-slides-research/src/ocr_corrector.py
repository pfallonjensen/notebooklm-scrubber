"""
OCR Error Correction Module

Two-stage pipeline:
1. Regex pre-filter for known error patterns (fast, free)
2. Claude Sonnet 4 for context-aware corrections (quality)
"""

import re
import os
from typing import List, Dict, Tuple, Optional

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False


# Stage 1: Known OCR error patterns (regex-based)
# Format: (pattern, replacement)
KNOWN_FIXES: List[Tuple[str, str]] = [
    # Character substitution errors
    (r'supplyyote', 'supply chain'),
    (r'inteligent', 'intelligent'),
    (r'\bROl\b', 'ROI'),  # lowercase L for uppercase I
    (r'\bRO1\b', 'ROI'),  # number 1 for uppercase I
    (r'\bl\b(?=\s*%)', 'I'),  # lowercase L before % (common in "15-25l%" → "15-25%")

    # Common OCR artifacts from icons/graphics
    (r'\bi\nS\b', ''),      # Icon misread as "i\nS"
    (r'\b→0\b', ''),        # Arrow symbol misread
    (r'^[→←↑↓]\d*$', ''),   # Single arrow with optional number

    # Line break issues
    (r'\n\s+', '\n'),       # Remove leading whitespace after newlines
    (r'\s+\n', '\n'),       # Remove trailing whitespace before newlines

    # Common word errors in business context
    (r'\bforecsat\b', 'forecast'),
    (r'\binventroy\b', 'inventory'),
    (r'\bmanagment\b', 'management'),
    (r'\banalsis\b', 'analysis'),
    (r'\boptimzation\b', 'optimization'),
    (r'\befficeint\b', 'efficient'),
    (r'\bautomtic\b', 'automatic'),
    (r'\boperatinal\b', 'operational'),
]

# Text patterns that are likely garbage (skip entirely)
GARBAGE_PATTERNS = [
    r'^i\nS$',           # Icon misread
    r'^→\d*$',           # Arrow with optional number
    r'^[^\w\s]{1,3}$',   # Only 1-3 special characters
]


def apply_regex_fixes(text: str) -> Tuple[str, List[str]]:
    """
    Apply known regex-based fixes to text.

    Args:
        text: Input text with potential OCR errors

    Returns:
        Tuple of (corrected_text, list_of_fixes_applied)
    """
    fixes_applied = []
    result = text

    for pattern, replacement in KNOWN_FIXES:
        if re.search(pattern, result, re.IGNORECASE):
            new_result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
            if new_result != result:
                fixes_applied.append(f"'{pattern}' → '{replacement}'")
                result = new_result

    return result, fixes_applied


def is_garbage_text(text: str) -> bool:
    """Check if text should be skipped entirely (likely OCR garbage)."""
    text = text.strip()
    for pattern in GARBAGE_PATTERNS:
        if re.match(pattern, text):
            return True
    return False


def fix_with_sonnet(
    texts: List[str],
    slide_context: str = "",
    api_key: Optional[str] = None
) -> List[str]:
    """
    Fix OCR errors using Claude Sonnet 4.

    Batches multiple text blocks into a single API call for efficiency.

    Args:
        texts: List of text strings to correct
        slide_context: Optional context (e.g., slide title) for better corrections
        api_key: Anthropic API key (defaults to ANTHROPIC_API_KEY env var)

    Returns:
        List of corrected text strings (same order as input)
    """
    if not ANTHROPIC_AVAILABLE:
        print("Warning: anthropic package not installed. Skipping LLM correction.")
        return texts

    if not texts:
        return texts

    api_key = api_key or os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        print("Warning: No ANTHROPIC_API_KEY found. Skipping LLM correction.")
        return texts

    # Format texts for batch processing
    numbered_texts = "\n".join([f"[{i+1}] {t}" for i, t in enumerate(texts)])

    prompt = f"""Fix OCR errors in these text blocks from a business presentation slide.
Only fix obvious spelling/OCR mistakes. DO NOT change meaning, formatting, or line breaks.
Return ONLY the corrected texts in the same numbered format.

Context: {slide_context if slide_context else "Business presentation slide"}

Texts to correct:
{numbered_texts}

Return corrected texts (same numbered format):"""

    try:
        client = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}]
        )

        # Parse response
        response_text = response.content[0].text
        corrected = parse_numbered_response(response_text, len(texts))

        return corrected if len(corrected) == len(texts) else texts

    except Exception as e:
        print(f"Warning: Sonnet API call failed: {e}. Using uncorrected text.")
        return texts


def parse_numbered_response(response: str, expected_count: int) -> List[str]:
    """Parse numbered response from LLM back into list."""
    lines = response.strip().split('\n')
    results = []
    current_num = 1
    current_text = []

    for line in lines:
        # Check if this line starts a new numbered item
        match = re.match(r'\[(\d+)\]\s*(.*)', line)
        if match:
            num = int(match.group(1))
            if current_text and num != current_num:
                results.append('\n'.join(current_text))
                current_text = []
            current_num = num
            if match.group(2):
                current_text.append(match.group(2))
        elif current_text is not None:
            current_text.append(line)

    # Don't forget last item
    if current_text:
        results.append('\n'.join(current_text))

    return results


def correct_text(
    text: str,
    slide_context: str = "",
    use_llm: bool = True,
    api_key: Optional[str] = None
) -> str:
    """
    Full OCR correction pipeline for a single text.

    Stage 1: Apply regex fixes (fast, free)
    Stage 2: Apply Sonnet fixes if enabled (quality)

    Args:
        text: Text to correct
        slide_context: Context for better LLM corrections
        use_llm: Whether to use LLM for Stage 2
        api_key: Anthropic API key

    Returns:
        Corrected text
    """
    if is_garbage_text(text):
        return ""

    # Stage 1: Regex
    corrected, fixes = apply_regex_fixes(text)
    if fixes:
        print(f"  Regex fixes applied: {fixes}")

    # Stage 2: LLM (optional)
    if use_llm and corrected.strip():
        corrected = fix_with_sonnet([corrected], slide_context, api_key)[0]

    return corrected


def correct_texts_batch(
    texts: List[str],
    slide_context: str = "",
    use_llm: bool = True,
    api_key: Optional[str] = None
) -> List[str]:
    """
    Batch OCR correction for multiple texts (more efficient).

    Args:
        texts: List of texts to correct
        slide_context: Context for better LLM corrections
        use_llm: Whether to use LLM for Stage 2
        api_key: Anthropic API key

    Returns:
        List of corrected texts
    """
    results = []
    llm_candidates = []
    llm_indices = []

    # Stage 1: Apply regex fixes to all texts
    for i, text in enumerate(texts):
        if is_garbage_text(text):
            results.append("")
        else:
            corrected, _ = apply_regex_fixes(text)
            results.append(corrected)
            if corrected.strip():
                llm_candidates.append(corrected)
                llm_indices.append(i)

    # Stage 2: Batch LLM correction
    if use_llm and llm_candidates:
        llm_results = fix_with_sonnet(llm_candidates, slide_context, api_key)
        for idx, corrected in zip(llm_indices, llm_results):
            results[idx] = corrected

    return results


if __name__ == '__main__':
    # Test with sample OCR errors
    test_texts = [
        "Key Takeaway: Wesco's digital transformation journey presents an opportunity to build the industry's most agile and inteligent supplyyote",
        "Cut inventory carrying costs by 15-25% by aligning stock precisely with the latest demand reality.",
        "Improve forecast accuracy by 5-20% and establish a clear ROl.",
        "i\nS",  # Garbage
    ]

    print("Testing OCR Corrector")
    print("=" * 50)

    for text in test_texts:
        print(f"\nOriginal: {text[:60]}...")
        corrected = correct_text(text, use_llm=False)  # Regex only for test
        print(f"Corrected: {corrected[:60]}...")
