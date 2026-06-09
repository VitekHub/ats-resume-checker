from __future__ import annotations

from pathlib import Path
from typing import Any, cast

import fitz  # PyMuPDF
import pdfplumber

from ats_checker.config import Config
from ats_checker.models import ImageInfo


class PDFError(Exception):
    """Base exception for PDF processing errors."""


class PDFCorruptedError(PDFError):
    """Raised when a PDF file is corrupted or cannot be opened."""


class PDFPasswordError(PDFError):
    """Raised when a PDF file is password protected."""


class ExtractionError(PDFError):
    """Raised when an error occurs during text or image extraction."""


class PDFDocument:
    """
    A wrapper for PDF documents that coordinates both pdfplumber and PyMuPDF.
    Provides centralized loading, metadata access, and cached text extraction.
    """

    def __init__(self, path: Path) -> None:
        self.path = path
        self._pdfplumber_doc: Any | None = None
        self._fitz_doc: fitz.Document | None = None
        self._text_cache: dict[int, str] = {}

        try:
            self._pdfplumber_doc = pdfplumber.open(path)
            self._fitz_doc = fitz.open(path)
        except fitz.FileDataError as e:
            raise PDFCorruptedError(f"PDF file is corrupted: {e}") from e
        except fitz.PasswordError as e:
            raise PDFPasswordError(f"PDF file is password protected: {e}") from e
        except Exception as e:
            raise PDFCorruptedError(f"Failed to open PDF file: {e}") from e

    def __enter__(self) -> PDFDocument:
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.close()

    def close(self) -> None:
        """Close both PDF handles to release resources."""
        if self._pdfplumber_doc:
            self._pdfplumber_doc.close()
            self._pdfplumber_doc = None
        if self._fitz_doc:
            self._fitz_doc.close()
            self._fitz_doc = None

    @property
    def page_count(self) -> int:
        """Return the total number of pages in the document."""
        if self._fitz_doc is None:
            raise ExtractionError("PDF document is not open")
        return len(self._fitz_doc)

    @property
    def file_size_kb(self) -> float:
        """Return the file size in kilobytes."""
        return self.path.stat().st_size / 1024

    @property
    def metadata(self) -> dict[str, Any]:
        """Return the PDF metadata."""
        if self._fitz_doc is None:
            raise ExtractionError("PDF document is not open")
        return cast(dict[str, Any], self._fitz_doc.metadata)

    def get_page_text(self, page_index: int) -> str:
        """
        Extract text from a specific page, using a cache to avoid re-extraction.
        Page index is 0-based.
        """
        if page_index in self._text_cache:
            return self._text_cache[page_index]

        if self._pdfplumber_doc is None:
            raise ExtractionError("PDF document is not open")

        try:
            page = self._pdfplumber_doc.pages[page_index]
            text = page.extract_text() or ""
            self._text_cache[page_index] = text
            return text
        except Exception as e:
            raise ExtractionError(f"Failed to extract text from page {page_index}: {e}") from e


def extract_text(pdf: PDFDocument) -> str:
    """
    Extracts all text from all pages using pdfplumber.
    Returns concatenated text with form feed characters as page breaks.
    """
    pages_text = []
    for i in range(pdf.page_count):
        pages_text.append(pdf.get_page_text(i))

    return "\f".join(pages_text)


def extract_words(pdf: PDFDocument) -> list[dict[str, Any]]:
    """
    Extracts word-level data with position info.
    Returns a list of dictionaries containing text and bounding box coordinates.
    """
    words: list[dict[str, Any]] = []
    if pdf._pdfplumber_doc is None:
        raise ExtractionError("PDF document is not open")

    try:
        for page in pdf._pdfplumber_doc.pages:
            page_words = page.extract_words()
            # Ensure the result matches the expected format:
            # {"text": ..., "x0": ..., "x1": ..., "top": ..., "bottom": ...}
            for w in page_words:
                words.append(
                    {
                        "text": w["text"],
                        "x0": w["x0"],
                        "x1": w["x1"],
                        "top": w["top"],
                        "bottom": w["bottom"],
                    }
                )
    except Exception as e:
        raise ExtractionError(f"Failed to extract words: {e}") from e

    return words


def extract_images_info(pdf: PDFDocument, config: Config) -> list[ImageInfo]:
    """
    Extracts structured image data using PyMuPDF.
    Determines if an image is 'large' based on the provided configuration.
    """
    images_info: list[ImageInfo] = []
    if pdf._fitz_doc is None:
        raise ExtractionError("PDF document is not open")

    try:
        for page_index in range(pdf.page_count):
            page = pdf._fitz_doc[page_index]
            for img in page.get_images(full=True):
                xref = img[0]
                pix = fitz.Pixmap(pdf._fitz_doc, xref)

                width = pix.width
                height = pix.height

                is_large = (
                    width >= config.images.large_width_px or height >= config.images.large_height_px
                )

                images_info.append(
                    ImageInfo(
                        page=page_index + 1,
                        xref=xref,
                        width=width,
                        height=height,
                        is_large=is_large,
                    )
                )
    except Exception as e:
        raise ExtractionError(f"Failed to extract image information: {e}") from e

    return images_info


def extract_font_info(pdf: PDFDocument) -> set[str]:
    """
    Returns a normalized set of font names found in the document using PyMuPDF.
    """
    fonts: set[str] = set()
    if pdf._fitz_doc is None:
        raise ExtractionError("PDF document is not open")

    try:
        for page_index in range(pdf.page_count):
            page = pdf._fitz_doc[page_index]
            for font in page.get_fonts():
                # Normalize font names to lowercase and strip spaces
                font_name = font[3] if len(font) > 3 else font[0]
                name = font_name.lower().replace(" ", "")
                fonts.add(name)
    except Exception as e:
        raise ExtractionError(f"Failed to extract font information: {e}") from e

    return fonts
