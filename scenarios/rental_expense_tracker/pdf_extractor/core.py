"""
PDF extractor core functionality.

Extracts text from PDF files for processing.
"""

from pathlib import Path

import pypdf

from amplifier.utils.logger import get_logger

logger = get_logger(__name__)


class PDFExtractor:
    """Extracts text content from PDF files."""

    async def extract_text(self, pdf_path: Path) -> str:
        """Extract text from a PDF file.

        Args:
            pdf_path: Path to PDF file

        Returns:
            Extracted text content
        """
        try:
            with open(pdf_path, "rb") as file:
                reader = pypdf.PdfReader(file)
                text_parts = []

                for page_num, page in enumerate(reader.pages, 1):
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(f"--- Page {page_num} ---\n{page_text}")

                full_text = "\n\n".join(text_parts)
                logger.debug(f"Extracted {len(full_text)} characters from {pdf_path.name}")
                return full_text

        except Exception as e:
            logger.error(f"Failed to extract text from {pdf_path}: {e}")
            raise
