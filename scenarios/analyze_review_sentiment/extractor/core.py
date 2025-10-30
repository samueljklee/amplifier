"""
PDF text extraction functionality.

Extracts text content from PDF files containing customer reviews.
"""

from pathlib import Path

import pypdf

from amplifier.utils.logger import get_logger

logger = get_logger(__name__)


class PDFExtractor:
    """Extracts text from PDF files."""

    async def extract_text(self, pdf_path: Path) -> str:
        """Extract all text from a PDF file.

        Args:
            pdf_path: Path to PDF file

        Returns:
            Extracted text content

        Raises:
            FileNotFoundError: If PDF doesn't exist
            ValueError: If PDF cannot be read
        """
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")

        try:
            logger.info(f"Opening PDF: {pdf_path.name}")
            reader = pypdf.PdfReader(str(pdf_path))

            # Validate PDF
            if len(reader.pages) == 0:
                raise ValueError("PDF has no pages")

            logger.info(f"Extracting text from {len(reader.pages)} pages")

            # Extract text from all pages
            text_parts = []
            for i, page in enumerate(reader.pages):
                logger.debug(f"Processing page {i + 1}/{len(reader.pages)}")
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)

            full_text = "\n\n".join(text_parts)

            if not full_text.strip():
                raise ValueError("No text could be extracted from PDF")

            logger.info(f"Successfully extracted {len(full_text)} characters")
            return full_text

        except Exception as e:
            logger.error(f"Failed to extract text from PDF: {e}")
            raise ValueError(f"PDF extraction failed: {e}") from e
