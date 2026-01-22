#!/usr/bin/env python3
"""
PDF Processor - Extract content from PDFs using PyMuPDF
Extracts pages as images, embedded images, and text blocks with positioning
"""

import io
import fitz  # PyMuPDF
from PIL import Image
from typing import List, Dict, Tuple
from pathlib import Path

from config import config


class PDFProcessor:
    """Handle all PDF extraction operations"""

    def __init__(self):
        self.dpi = config.PDF_DPI

    def extract_pages_as_images(self, pdf_path: str) -> List[Image.Image]:
        """
        Convert PDF pages to PNG images for Gemini Vision analysis

        Args:
            pdf_path: Path to PDF file

        Returns:
            List of PIL Images (one per page)
        """
        doc = fitz.open(pdf_path)
        images = []

        for page_num in range(len(doc)):
            page = doc[page_num]

            # Convert page to pixmap (raster image)
            pix = page.get_pixmap(dpi=self.dpi)

            # Convert pixmap to PIL Image
            img_bytes = pix.tobytes("png")
            img = Image.open(io.BytesIO(img_bytes))

            # Check size - resize if needed (Gemini 4MB limit)
            size_mb = len(img_bytes) / (1024 * 1024)
            if size_mb > config.MAX_IMAGE_SIZE_MB:
                # Reduce quality while maintaining aspect ratio
                reduction_factor = (config.MAX_IMAGE_SIZE_MB / size_mb) ** 0.5
                new_width = int(img.width * reduction_factor)
                new_height = int(img.height * reduction_factor)
                img = img.resize((new_width, new_height), Image.LANCZOS)

            images.append(img)

        doc.close()
        return images

    def extract_embedded_images(self, pdf_path: str, page_num: int) -> List[Dict]:
        """
        Extract embedded images from a specific page

        Args:
            pdf_path: Path to PDF file
            page_num: Page number (0-indexed)

        Returns:
            List of dicts with keys:
            - image_bytes: Image data as bytes
            - bbox: Bounding box (x0, y0, x1, y1) in PDF points
            - index: Image index on page
            - format: Image format (png, jpeg, etc)
        """
        doc = fitz.open(pdf_path)
        page = doc[page_num]

        images = []
        image_list = page.get_images(full=True)

        for img_index, img_info in enumerate(image_list):
            xref = img_info[0]  # Image xref

            # Extract image
            base_image = doc.extract_image(xref)
            image_bytes = base_image["image"]
            image_ext = base_image["ext"]

            # Get image position on page using get_image_rects
            try:
                rects = page.get_image_rects(xref)
                if rects:
                    # Use first rectangle if image appears multiple times
                    bbox = tuple(rects[0])
                else:
                    # Fallback: use full page dimensions
                    bbox = (0, 0, page.rect.width, page.rect.height)
            except:
                # Fallback if method not available
                bbox = (0, 0, page.rect.width, page.rect.height)

            images.append({
                "image_bytes": image_bytes,
                "bbox": bbox,  # (x0, y0, x1, y1)
                "index": img_index,
                "format": image_ext
            })

        doc.close()
        return images

    def extract_text_blocks(self, pdf_path: str, page_num: int) -> List[Dict]:
        """
        Extract text blocks with formatting and positioning

        Args:
            pdf_path: Path to PDF file
            page_num: Page number (0-indexed)

        Returns:
            List of dicts with keys:
            - text: Text content
            - bbox: Bounding box (x0, y0, x1, y1) in PDF points
            - font_size: Font size in points
            - font_name: Font name
            - font_flags: Font flags (bold, italic, etc)
        """
        doc = fitz.open(pdf_path)
        page = doc[page_num]

        # Get text in dictionary format (structured)
        text_dict = page.get_text("dict")

        text_blocks = []

        # Extract text blocks from structured format
        for block in text_dict["blocks"]:
            # Only process text blocks (not image blocks)
            if block.get("type") == 0:  # 0 = text block
                for line in block.get("lines", []):
                    for span in line.get("spans", []):
                        text_blocks.append({
                            "text": span["text"],
                            "bbox": tuple(span["bbox"]),  # (x0, y0, x1, y1)
                            "font_size": span["size"],
                            "font_name": span["font"],
                            "font_flags": span["flags"],  # Bold, italic, etc
                            "color": span.get("color", 0)  # Text color
                        })

        doc.close()
        return text_blocks

    def get_page_metadata(self, pdf_path: str) -> Dict:
        """
        Get PDF metadata (page count, dimensions, orientation)

        Args:
            pdf_path: Path to PDF file

        Returns:
            Dict with metadata
        """
        doc = fitz.open(pdf_path)

        # Get first page dimensions (assume all pages same size)
        first_page = doc[0]
        rect = first_page.rect

        metadata = {
            "page_count": len(doc),
            "page_width": rect.width,
            "page_height": rect.height,
            "orientation": "landscape" if rect.width > rect.height else "portrait",
            "filename": Path(pdf_path).name
        }

        doc.close()
        return metadata

    def extract_page_complete(self, pdf_path: str, page_num: int) -> Dict:
        """
        Extract all content from a single page (images, text, metadata)

        Args:
            pdf_path: Path to PDF file
            page_num: Page number (0-indexed)

        Returns:
            Dict with all extracted content
        """
        return {
            "page_num": page_num,
            "text_blocks": self.extract_text_blocks(pdf_path, page_num),
            "images": self.extract_embedded_images(pdf_path, page_num),
            "metadata": self.get_page_metadata(pdf_path)
        }


if __name__ == "__main__":
    """Test PDF processor"""
    import sys

    if len(sys.argv) < 2:
        print("Usage: python3 pdf_processor.py <pdf_file>")
        sys.exit(1)

    pdf_file = sys.argv[1]
    if not Path(pdf_file).exists():
        print(f"Error: File not found: {pdf_file}")
        sys.exit(1)

    print(f"=== Testing PDF Processor ===\n")
    print(f"Processing: {pdf_file}\n")

    processor = PDFProcessor()

    # Get metadata
    metadata = processor.get_page_metadata(pdf_file)
    print(f"Pages: {metadata['page_count']}")
    print(f"Dimensions: {metadata['page_width']} x {metadata['page_height']} pts")
    print(f"Orientation: {metadata['orientation']}\n")

    # Extract first page
    print("Extracting page 1...")
    page_images = processor.extract_pages_as_images(pdf_file)
    print(f"✓ Extracted {len(page_images)} page images")
    print(f"  First page size: {page_images[0].size} pixels\n")

    text_blocks = processor.extract_text_blocks(pdf_file, 0)
    print(f"✓ Extracted {len(text_blocks)} text blocks")
    if text_blocks:
        print(f"  Sample text: '{text_blocks[0]['text'][:50]}...'\n")

    images = processor.extract_embedded_images(pdf_file, 0)
    print(f"✓ Extracted {len(images)} embedded images")
    if images:
        print(f"  First image: {images[0]['format']}, bbox: {images[0]['bbox']}\n")

    print("✅ PDF Processor test complete!")
