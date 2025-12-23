#!/usr/bin/env python3
"""
NotebookLM Logo Scrubber
Removes the NotebookLM watermark from PDF slide decks exported from NotebookLM.
The logo appears in the bottom-right corner of each page's footer.

Usage:
    python3 scrub-notebooklm-logo.py input.pdf [output.pdf]

If output.pdf is not specified, creates input_clean.pdf
"""

import sys
import os
import io
import fitz  # PyMuPDF
from PIL import Image


def sample_color_averaged(pix, x, y, radius=2):
    """Sample and average colors in a small area to reduce noise."""
    colors = []
    for dx in range(-radius, radius + 1):
        for dy in range(-radius, radius + 1):
            sx = max(0, min(int(x + dx), pix.width - 1))
            sy = max(0, min(int(y + dy), pix.height - 1))
            pixel = pix.pixel(sx, sy)
            colors.append((pixel[0], pixel[1], pixel[2]))

    # Average all sampled colors
    avg = tuple(sum(c[i] for c in colors) // len(colors) for i in range(3))
    return avg


def create_gradient_overlay(pix, logo_left, logo_top, page_width, page_height):
    """
    Create a gradient image that blends smoothly with surrounding colors.
    Samples colors around the logo area edges and creates a smooth gradient
    using bilinear interpolation.
    """
    # Logo area dimensions
    logo_width = int(page_width - logo_left)
    logo_height = int(page_height - logo_top)

    # Sample colors at key points around the logo area (averaged to reduce noise)
    # Left edge: sample at multiple heights
    left_top = sample_color_averaged(pix, logo_left - 2, logo_top + 2)
    left_bot = sample_color_averaged(pix, logo_left - 2, page_height - 2)

    # Top edge: sample at multiple positions
    top_left = sample_color_averaged(pix, logo_left + 2, logo_top - 2)
    top_right = sample_color_averaged(pix, page_width - 2, logo_top - 2)

    # Create gradient image (RGB, fully opaque)
    gradient = Image.new('RGB', (logo_width, logo_height))

    for y in range(logo_height):
        for x in range(logo_width):
            # Normalized positions (0 to 1)
            nx = x / max(logo_width - 1, 1)
            ny = y / max(logo_height - 1, 1)

            # Interpolate left edge color (vertical)
            left_color = tuple(
                int(left_top[c] * (1 - ny) + left_bot[c] * ny)
                for c in range(3)
            )

            # Interpolate top edge color (horizontal)
            top_color = tuple(
                int(top_left[c] * (1 - nx) + top_right[c] * nx)
                for c in range(3)
            )

            # Blend: weight left edge more at left, top edge more at top
            weight_left = 1 - nx
            weight_top = 1 - ny

            # Normalize weights
            total_weight = weight_left + weight_top
            if total_weight > 0:
                weight_left /= total_weight
                weight_top /= total_weight
            else:
                weight_left = weight_top = 0.5

            # Final blended color
            final_color = tuple(
                int(left_color[c] * weight_left + top_color[c] * weight_top)
                for c in range(3)
            )

            gradient.putpixel((x, y), final_color)

    return gradient


def scrub_logo(input_path, output_path=None):
    """
    Remove NotebookLM logo from each page of a PDF.

    Args:
        input_path: Path to input PDF
        output_path: Path for output PDF (default: input_clean.pdf)

    Returns:
        Path to the cleaned PDF
    """
    if output_path is None:
        base, ext = os.path.splitext(input_path)
        output_path = f"{base}_clean{ext}"

    # Open the PDF
    doc = fitz.open(input_path)

    # Logo area bounds (bottom-right corner)
    # These are in PDF points (same as pixels at 72 DPI)
    # NotebookLM logo is small icon in far right corner (~100px wide)
    # Tuned for standard NotebookLM slide export dimensions (1366x768)
    LOGO_LEFT = 1269   # Start covering from here
    LOGO_TOP = 747     # Top of cover area
    # Right and bottom extend to page edge

    pages_processed = 0

    for page_num in range(len(doc)):
        page = doc[page_num]
        page_width = page.rect.width
        page_height = page.rect.height

        # Get pixmap for color sampling
        pix = page.get_pixmap(dpi=72)

        # Create gradient overlay that blends with surrounding colors
        gradient = create_gradient_overlay(pix, LOGO_LEFT, LOGO_TOP, page_width, page_height)

        # Convert PIL image to bytes for PyMuPDF
        img_buffer = io.BytesIO()
        gradient.save(img_buffer, format='PNG')
        img_buffer.seek(0)

        # Define the rectangle where the overlay goes
        logo_rect = fitz.Rect(
            LOGO_LEFT,
            LOGO_TOP,
            page_width,
            page_height
        )

        # Insert the gradient image over the logo area
        page.insert_image(logo_rect, stream=img_buffer.getvalue())

        pages_processed += 1

    # Save the modified PDF
    doc.save(output_path, garbage=4, deflate=True)
    doc.close()

    print(f"Processed {pages_processed} pages")
    print(f"Saved to: {output_path}")

    return output_path


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 scrub-notebooklm-logo.py input.pdf [output.pdf]")
        sys.exit(1)

    input_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else None

    if not os.path.exists(input_path):
        print(f"Error: File not found: {input_path}")
        sys.exit(1)

    scrub_logo(input_path, output_path)


if __name__ == "__main__":
    main()
