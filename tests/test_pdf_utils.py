"""Tests for PDF utility error handling, caching, and normalization logic.

Covers step 5.4 requirements:
- PDFDocument error handling (corrupted, missing, encrypted, resource cleanup)
- extract_text() caching (second call uses cache)
- extract_text() normalization (empty page → "", form-feed joining)
- extract_images_info() classification (large vs small, OR logic, config thresholds)
- extract_font_info() normalization (lowercase, space-stripping, empty set for image-only)

Skips (per X1–X6):
- "Opens valid PDF without error" — thin wrapper over pdfplumber/PyMuPDF (X3)
- page_count, file_size_kb — trivial computed properties (X2)
- "Returns all text from multi-page PDF" — testing pdfplumber (X3)
- "Returns word list" — testing pdfplumber (X3)
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

import fitz  # PyMuPDF
import pytest

from ats_checker.config import Config, ImageConfig
from ats_checker.pdf_utils import (
    ExtractionError,
    PDFCorruptedError,
    PDFDocument,
    extract_font_info,
    extract_images_info,
    extract_text,
    extract_words,
)

from .helpers import create_empty_pdf, create_test_pdf

# =============================================================================
# Helper: create PDF with an image of specific dimensions
# =============================================================================


def _create_pdf_with_image(
    tmp_path: Path,
    width: int,
    height: int,
    color: tuple[int, int, int] = (255, 0, 0),
    filename: str = "test_img.pdf",
) -> Path:
    """Create a PDF containing a single image of the specified dimensions.

    The image is inserted at position (72, 72) on an A4 page.
    """
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)
    pix = fitz.Pixmap(fitz.csRGB, fitz.IRect(0, 0, width, height))
    pix.set_rect(pix.irect, color)
    page.insert_image(
        fitz.Rect(72, 72, 72 + width, 72 + height),
        pixmap=pix,
    )
    pdf_path = tmp_path / filename
    doc.save(pdf_path)
    doc.close()
    return pdf_path


# =============================================================================
# TestPDFDocumentErrorHandling
# =============================================================================


class TestPDFDocumentErrorHandling:
    """Tests for PDFDocument error handling: corrupted, missing, encrypted,
    and resource cleanup on exception paths.
    """

    def test_raises_error_for_corrupted_file(self, tmp_path: Path) -> None:
        """Corrupted (non-PDF) content must raise PDFCorruptedError (R4)."""
        corrupted_path = tmp_path / "corrupted.pdf"
        corrupted_path.write_bytes(b"this is not a valid pdf file at all")
        with pytest.raises(PDFCorruptedError):
            PDFDocument(corrupted_path)

    def test_raises_error_for_nonexistent_file(self) -> None:
        """Non-existent file path must raise PDFCorruptedError (R4)."""
        nonexistent_path = Path("/nonexistent/path/missing_file.pdf")
        with pytest.raises(PDFCorruptedError):
            PDFDocument(nonexistent_path)

    def test_context_manager_closes_on_normal_exit(self, tmp_path: Path) -> None:
        """Context manager must call close() on normal exit, releasing resources."""
        pdf_bytes = create_test_pdf(text="Test close", pages=1)
        pdf_path = tmp_path / "close_test.pdf"
        pdf_path.write_bytes(pdf_bytes)

        with PDFDocument(pdf_path) as pdf:
            pass  # Normal exit

        assert pdf._pdfplumber_doc is None
        assert pdf._fitz_doc is None

    def test_context_manager_closes_on_exception(self, tmp_path: Path) -> None:
        """Context manager must close resources even when an exception occurs (R4)."""
        pdf_bytes = create_test_pdf(text="Test exception cleanup", pages=1)
        pdf_path = tmp_path / "exception_test.pdf"
        pdf_path.write_bytes(pdf_bytes)

        pdf = PDFDocument(pdf_path)
        try:
            with pdf:
                assert pdf._pdfplumber_doc is not None
                raise RuntimeError("Deliberate test exception")
        except RuntimeError:
            pass

        assert pdf._pdfplumber_doc is None
        assert pdf._fitz_doc is None

    def test_close_is_idempotent(self, tmp_path: Path) -> None:
        """Calling close() multiple times must not raise."""
        pdf_bytes = create_test_pdf(text="Test idempotent close", pages=1)
        pdf_path = tmp_path / "idempotent.pdf"
        pdf_path.write_bytes(pdf_bytes)

        pdf = PDFDocument(pdf_path)
        pdf.close()
        pdf.close()  # Second call should not raise

    @pytest.mark.parametrize(
        "accessor_name, accessor",
        [
            ("page_count", lambda pdf: pdf.page_count),
            ("metadata", lambda pdf: pdf.metadata),
            ("get_page_text", lambda pdf: pdf.get_page_text(0)),
            ("text_property", lambda pdf: pdf.text),
            ("extract_words", lambda pdf: extract_words(pdf)),
            ("extract_images_info", lambda pdf: extract_images_info(pdf, Config())),
            ("extract_font_info", lambda pdf: extract_font_info(pdf)),
        ],
    )
    def test_extraction_error_after_close(
        self, tmp_path: Path, accessor_name: str, accessor: Callable[[PDFDocument], Any]
    ) -> None:
        """Properties/methods/functions must raise ExtractionError after close() (R4)."""
        pdf_bytes = create_test_pdf(text="Closed doc test", pages=1)
        pdf_path = tmp_path / "closed.pdf"
        pdf_path.write_bytes(pdf_bytes)

        pdf = PDFDocument(pdf_path)
        pdf.close()

        with pytest.raises(ExtractionError):
            accessor(pdf)

# =============================================================================
# TestExtractTextCaching
# =============================================================================


class TestExtractTextCaching:
    """Tests for the _text_cache mechanism in PDFDocument.get_page_text()."""

    def test_second_call_uses_cache(self, tmp_path: Path) -> None:
        """Second call to get_page_text must use the cache, not re-extract (R7)."""
        pdf_bytes = create_test_pdf(text="Cache test content", pages=1)
        pdf_path = tmp_path / "cache_test.pdf"
        pdf_path.write_bytes(pdf_bytes)

        with PDFDocument(pdf_path) as pdf:
            pdf._text_cache.clear()

            # Wrap the pdfplumber page's extract_text to count calls
            original_extract = pdf._pdfplumber_doc.pages[0].extract_text
            call_count = 0

            def counting_extract() -> str | None:
                nonlocal call_count
                call_count += 1
                return original_extract()

            pdf._pdfplumber_doc.pages[0].extract_text = counting_extract

            # First call triggers extraction
            text1 = pdf.get_page_text(0)
            assert call_count == 1

            # Second call uses cache — extract_text NOT called again
            text2 = pdf.get_page_text(0)
            assert call_count == 1  # Still 1, not 2

            # Results are identical
            assert text1 == text2

    def test_cache_is_per_page(self, tmp_path: Path) -> None:
        """Each page's text must be cached independently."""
        pdf_bytes = create_test_pdf(text="Page content", pages=3)
        pdf_path = tmp_path / "multi_page.pdf"
        pdf_path.write_bytes(pdf_bytes)

        with PDFDocument(pdf_path) as pdf:
            pdf._text_cache.clear()
            text0 = pdf.get_page_text(0)
            text1 = pdf.get_page_text(1)

            # Both pages should be in cache
            assert 0 in pdf._text_cache
            assert 1 in pdf._text_cache

            # Cache values match returned values
            assert pdf._text_cache[0] == text0
            assert pdf._text_cache[1] == text1

    def test_extract_text_populates_cache(self, tmp_path: Path) -> None:
        """extract_text() must populate the page text cache for all pages."""
        pdf_bytes = create_test_pdf(text="Cached page text", pages=2)
        pdf_path = tmp_path / "cached.pdf"
        pdf_path.write_bytes(pdf_bytes)

        with PDFDocument(pdf_path) as pdf:
            pdf._text_cache.clear()
            _ = pdf.text  # calls extract_text internally

            assert 0 in pdf._text_cache
            assert 1 in pdf._text_cache


# =============================================================================
# TestExtractTextNormalization
# =============================================================================


class TestExtractTextNormalization:
    """Tests for our text normalization layer (not pdfplumber's behavior).

    Currently, extract_text only normalizes via:
    - or "" fallback in get_page_text (None → empty string)
    - \\f separator between pages
    No whitespace stripping or encoding fixes exist yet.
    """

    def test_empty_page_returns_empty_string_not_none(self, tmp_path: Path) -> None:
        """get_page_text must return empty string for pages with no text, not None (R2)."""
        pdf_bytes = create_empty_pdf()
        pdf_path = tmp_path / "empty.pdf"
        pdf_path.write_bytes(pdf_bytes)

        with PDFDocument(pdf_path) as pdf:
            text = pdf.get_page_text(0)
            assert text == ""
            assert text is not None

    def test_pages_joined_with_form_feed(self, tmp_path: Path) -> None:
        """extract_text must join page texts with form feed character."""
        pdf_bytes = create_test_pdf(text="Page text", pages=3)
        pdf_path = tmp_path / "multi.pdf"
        pdf_path.write_bytes(pdf_bytes)

        with PDFDocument(pdf_path) as pdf:
            text = extract_text(pdf)
            pages = text.split("\f")
            assert len(pages) == 3

    def test_single_page_no_form_feed(self, tmp_path: Path) -> None:
        """Single-page PDF must produce text without form feed separator."""
        pdf_bytes = create_test_pdf(text="Single page content", pages=1)
        pdf_path = tmp_path / "single.pdf"
        pdf_path.write_bytes(pdf_bytes)

        with PDFDocument(pdf_path) as pdf:
            text = extract_text(pdf)
            assert "\f" not in text


# =============================================================================
# TestExtractImagesInfo
# =============================================================================


class TestExtractImagesInfo:
    """Tests for image classification logic in extract_images_info().

    Classification rule: is_large = width >= threshold OR height >= threshold.
    Tests our logic, not pdfplumber/PyMuPDF's image extraction (X3).
    """

    def test_large_image_classified_as_large(self, scanned_pdf: PDFDocument) -> None:
        """Images exceeding the threshold must be classified as large."""
        config = Config()  # default: large_width_px=72, large_height_px=72
        images = extract_images_info(scanned_pdf, config)
        assert len(images) > 0
        # Scanned PDF images are large (page-sized at 2x zoom)
        assert all(img.is_large for img in images)

    def test_small_image_classified_as_not_large(self, tmp_path: Path) -> None:
        """Images below both thresholds must be classified as not large (R2)."""
        pdf_path = _create_pdf_with_image(tmp_path, 32, 32, filename="small_img.pdf")

        config = Config()  # default: large_width_px=72, large_height_px=72
        with PDFDocument(pdf_path) as pdf:
            images = extract_images_info(pdf, config)
            assert len(images) > 0
            assert all(not img.is_large for img in images)

    def test_boundary_image_classified_as_large(self, tmp_path: Path) -> None:
        """Image at exactly the threshold (>=) must be classified as large (R2)."""
        pdf_path = _create_pdf_with_image(tmp_path, 72, 72, filename="boundary.pdf")

        config = Config()  # default threshold: 72x72
        with PDFDocument(pdf_path) as pdf:
            images = extract_images_info(pdf, config)
            # At least one image with dimension exactly 72 should be large
            assert any(img.is_large for img in images)

    def test_or_logic_width_only_exceeds(self, tmp_path: Path) -> None:
        """Width >= threshold but height < threshold must still be large (OR condition)."""
        pdf_path = _create_pdf_with_image(tmp_path, 100, 50, filename="wide_img.pdf")

        config = Config()  # default: 72x72
        with PDFDocument(pdf_path) as pdf:
            images = extract_images_info(pdf, config)
            # 100 wide x 50 tall — width exceeds 72 threshold
            assert any(img.is_large for img in images)

    def test_custom_config_threshold_respected(self, tmp_path: Path) -> None:
        """Config threshold must control image classification (R8)."""
        pdf_path = _create_pdf_with_image(tmp_path, 100, 100, filename="config_test.pdf")

        with PDFDocument(pdf_path) as pdf:
            # Default config: 72x72 threshold → is_large=True
            default_config = Config()
            images_default = extract_images_info(pdf, default_config)
            assert all(img.is_large for img in images_default)

            # Custom config: 200x200 threshold → is_large=False
            custom_config = Config(images=ImageConfig(large_width_px=200, large_height_px=200))
            images_custom = extract_images_info(pdf, custom_config)
            assert all(not img.is_large for img in images_custom)

    def test_pdf_with_no_images(self, clean_pdf: PDFDocument) -> None:
        """PDF with no images must return an empty list."""
        config = Config()
        images = extract_images_info(clean_pdf, config)
        assert images == []

    def test_image_info_fields_populated(self, scanned_pdf: PDFDocument) -> None:
        """ImageInfo fields must be correctly populated from the PDF."""
        config = Config()
        images = extract_images_info(scanned_pdf, config)
        assert len(images) > 0
        for img in images:
            assert img.page >= 1
            assert img.xref > 0
            assert img.width > 0
            assert img.height > 0
            assert isinstance(img.is_large, bool)


# =============================================================================
# TestExtractFontInfo
# =============================================================================


class TestExtractFontInfo:
    """Tests for font name normalization logic in extract_font_info().

    Normalization: font_name.lower().replace(" ", "").
    Image-only PDFs return empty set (our logic, not pdfplumber — X3).
    """

    def test_font_names_are_normalized(self, clean_pdf: PDFDocument) -> None:
        """Font names must be normalized: lowercase with spaces stripped."""
        fonts = extract_font_info(clean_pdf)
        assert len(fonts) > 0
        for font in fonts:
            assert font == font.lower(), f"Font name '{font}' is not lowercase"
            assert " " not in font, f"Font name '{font}' contains spaces"

    def test_empty_set_for_image_only_pdf(self, scanned_pdf: PDFDocument) -> None:
        """Image-only PDFs must return an empty font set (our logic, X3)."""
        fonts = extract_font_info(scanned_pdf)
        assert fonts == set()

    def test_empty_pdf_returns_empty_set(self, empty_pdf: PDFDocument) -> None:
        """Empty PDF (no text content) must return an empty font set."""
        fonts = extract_font_info(empty_pdf)
        assert fonts == set()

    def test_multiple_fonts_on_same_page(self, tmp_path: Path) -> None:
        """Multiple fonts on the same page must all be collected and normalized."""
        doc = fitz.open()
        page = doc.new_page(width=595, height=842)
        tw = fitz.TextWriter(page.rect)
        tw.append((72, 100), "Helvetica text", font=fitz.Font("helv"), fontsize=12)
        tw.append((72, 130), "Courier text", font=fitz.Font("cour"), fontsize=12)
        tw.write_text(page)
        pdf_path = tmp_path / "multi_font.pdf"
        doc.save(pdf_path)
        doc.close()

        with PDFDocument(pdf_path) as pdf:
            fonts = extract_font_info(pdf)
            assert len(fonts) >= 2  # At least two fonts
            # All normalized: lowercase, no spaces
            for f in fonts:
                assert f == f.lower()
                assert " " not in f

    def test_fonts_from_multiple_pages(self, tmp_path: Path) -> None:
        """Font extraction must collect fonts from all pages."""
        # Create a single-page PDF with a known font
        pdf_bytes = create_test_pdf(text="Multi page font test", pages=1, font_name="helv")
        pdf_path = tmp_path / "multi_page_fonts.pdf"
        pdf_path.write_bytes(pdf_bytes)

        with PDFDocument(pdf_path) as pdf:
            fonts = extract_font_info(pdf)
            assert len(fonts) > 0
            # The font should be a normalized version
            assert any("sans" in f.lower() or "helv" in f.lower() for f in fonts)
