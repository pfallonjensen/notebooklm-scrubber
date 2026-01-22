#!/usr/bin/env python3
"""
Vision Analyzer - Analyze PDF page structure using Gemini Vision API
Understands layout, hierarchy, and visual structure of presentation slides
"""

import json
import time
import io
from typing import Dict, Optional
from PIL import Image
from google import genai
from google.genai import types

from config import config


class VisionAnalyzer:
    """Analyze presentation slide structure using Gemini Vision"""

    # Prompt for structure analysis
    STRUCTURE_PROMPT = """
You are analyzing a presentation slide to understand its structure and layout.
Analyze this slide image and return ONLY valid JSON (no markdown, no explanations) with this exact structure:

{
  "page_type": "<title_slide|content_slide|section_header>",
  "title": "<main title text or empty string>",
  "subtitle": "<subtitle text or empty string>",
  "content_blocks": [
    {
      "type": "<text|bullet_list|numbered_list|image|table|chart>",
      "position": {
        "x": <0.0-1.0 normalized left position>,
        "y": <0.0-1.0 normalized top position>,
        "width": <0.0-1.0 normalized width>,
        "height": <0.0-1.0 normalized height>
      },
      "hierarchy_level": <1-3, where 1=main, 2=sub, 3=detail>,
      "content": "<text content or description of visual element>",
      "items": ["<item1>", "<item2>"] // Only for bullet/numbered lists
    }
  ],
  "layout": "<single_column|two_column|three_column|title_only|custom>",
  "visual_hierarchy": ["<element1>", "<element2>"] // Reading order
}

Focus on STRUCTURE and CONTENT, not styling. Be precise with positioning (use relative coordinates 0.0-1.0).
Return ONLY the JSON, nothing else.
"""

    def __init__(self):
        """Initialize Gemini API"""
        self.client = genai.Client(api_key=config.GEMINI_API_KEY)

    def analyze_page_structure(self, page_image: Image.Image, page_num: int) -> Dict:
        """
        Analyze slide structure using Gemini Vision

        Args:
            page_image: PIL Image of the slide
            page_num: Page number (1-indexed for logging)

        Returns:
            Dict with structured slide data (see STRUCTURE_PROMPT for schema)

        Raises:
            Exception: If API call fails after retries
        """
        retries = 0
        last_error = None

        while retries <= config.GEMINI_MAX_RETRIES:
            try:
                # Convert PIL Image to bytes
                img_bytes = io.BytesIO()
                page_image.save(img_bytes, format='PNG')
                img_bytes.seek(0)

                # Create image part
                image_part = types.Part.from_bytes(
                    data=img_bytes.getvalue(),
                    mime_type='image/png'
                )

                # Generate content from image + prompt using new API
                response = self.client.models.generate_content(
                    model=config.GEMINI_MODEL,
                    contents=[self.STRUCTURE_PROMPT, image_part],
                    config=types.GenerateContentConfig(
                        temperature=config.GEMINI_TEMPERATURE,
                        response_mime_type="application/json"
                    )
                )

                # Parse JSON response
                result = json.loads(response.text)

                # Validate required fields
                required_fields = ["page_type", "title", "content_blocks", "layout"]
                if not all(field in result for field in required_fields):
                    raise ValueError(f"Missing required fields in response: {result}")

                return result

            except json.JSONDecodeError as e:
                last_error = f"Invalid JSON response: {e}"
                print(f"⚠️  Page {page_num}: {last_error}")
                # Try to extract JSON from response
                try:
                    # Sometimes response has markdown code blocks
                    text = response.text.strip()
                    if text.startswith("```"):
                        text = text.split("```")[1]
                        if text.startswith("json"):
                            text = text[4:]
                        result = json.loads(text.strip())
                        return result
                except:
                    pass

            except Exception as e:
                last_error = f"API error: {e}"
                print(f"⚠️  Page {page_num}: {last_error}")

                # Check for rate limit (429 error)
                if "429" in str(e) or "quota" in str(e).lower():
                    wait_time = config.GEMINI_RETRY_DELAY * (2 ** retries)
                    print(f"   Rate limited. Waiting {wait_time}s before retry...")
                    time.sleep(wait_time)

            retries += 1

        # All retries exhausted
        raise Exception(
            f"Failed to analyze page {page_num} after {config.GEMINI_MAX_RETRIES} retries. "
            f"Last error: {last_error}"
        )

    def analyze_page_fallback(self, page_num: int) -> Dict:
        """
        Fallback structure when Vision analysis fails
        Returns minimal structure for text-only slides

        Args:
            page_num: Page number (1-indexed)

        Returns:
            Minimal structure dict
        """
        return {
            "page_type": "content_slide",
            "title": f"Slide {page_num}",
            "subtitle": "",
            "content_blocks": [],
            "layout": "single_column",
            "visual_hierarchy": ["title"]
        }


def test_vision_analyzer(image_path: str):
    """Test vision analyzer with an image file"""
    if not Path(image_path).exists():
        print(f"Error: Image not found: {image_path}")
        return

    print(f"=== Testing Vision Analyzer ===\n")
    print(f"Image: {image_path}\n")

    # Load image
    img = Image.open(image_path)
    print(f"Image size: {img.size} pixels\n")

    # Analyze
    analyzer = VisionAnalyzer()
    print("Analyzing structure with Gemini Vision...")

    try:
        result = analyzer.analyze_page_structure(img, page_num=1)
        print("\n✅ Analysis complete!\n")
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(f"\n❌ Analysis failed: {e}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python3 vision_analyzer.py <image_file>")
        print("Example: python3 vision_analyzer.py sample_slide.png")
        sys.exit(1)

    test_vision_analyzer(sys.argv[1])
