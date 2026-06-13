"""Pytest configuration and shared fixtures for ATS Resume Checker tests.

Provides:
- Configuration fixtures with test defaults
- PDF document fixtures for various test scenarios
- Temporary file management
"""

from __future__ import annotations

from pathlib import Path

import fitz  # PyMuPDF
import pytest

from ats_checker.config import (
    Config,
    FileSizeConfig,
    FontConfig,
    ImageConfig,
    LayoutConfig,
    MetadataConfig,
    OutputConfig,
    SectionConfig,
    TextExtractionConfig,
    UnicodeConfig,
)
from ats_checker.models import Severity
from ats_checker.pdf_utils import PDFDocument

from .helpers import (
    create_empty_pdf,
    create_large_pdf,
    create_multicolumn_pdf,
    create_pdf_with_metadata,
    create_pdf_with_special_chars,
    create_scanned_pdf,
    create_test_pdf,
)

# =============================================================================
# Configuration Fixtures
# =============================================================================


@pytest.fixture
def sample_config() -> Config:
    """Return a Config with test-friendly defaults.

    Uses color_output=False for deterministic test output.
    """
    return Config(
        file_size=FileSizeConfig(warning_kb=500, critical_kb=1024),
        images=ImageConfig(large_width_px=72, large_height_px=72),
        layout=LayoutConfig(min_words_for_column_check=20, column_gap_threshold=100),
        text=TextExtractionConfig(
            min_length_critical=50, alpha_ratio_critical=0.4, alpha_ratio_warning=0.6
        ),
        sections=SectionConfig(),
        fonts=FontConfig(),
        metadata=MetadataConfig(),
        output=OutputConfig(format="terminal", color_output=False, verbose=True),
        unicode=UnicodeConfig(),
    )


@pytest.fixture
def strict_text_config() -> Config:
    """Config with stricter text extraction thresholds.

    Useful for testing edge cases in text extraction checkers.
    """
    return Config(
        text=TextExtractionConfig(
            min_length_critical=100, alpha_ratio_critical=0.5, alpha_ratio_warning=0.7
        ),
    )


@pytest.fixture
def lenient_filesize_config() -> Config:
    """Config with more lenient file size thresholds.

    Useful for testing that large PDFs pass with higher thresholds.
    """
    return Config(
        file_size=FileSizeConfig(warning_kb=1000, critical_kb=2048),
    )


# =============================================================================
# PDF Document Fixtures
# =============================================================================


@pytest.fixture
def clean_pdf(tmp_path: Path) -> PDFDocument:
    """Create a well-formed, text-based PDF resume.

    This is the happy path fixture — a clean resume that should
    pass most ATS checks.
    """
    content = create_test_pdf(
        text=(
            "John Doe\n"
            "Software Engineer\n"
            "john.doe@example.com | (555) 123-4567\n"
            "\n"
            "EXPERIENCE\n"
            "Senior Developer at Tech Corp (2020-Present)\n"
            "- Led development of microservices architecture\n"
            "- Mentored junior developers\n"
            "\n"
            "EDUCATION\n"
            "B.S. Computer Science, State University (2016)\n"
            "\n"
            "SKILLS\n"
            "Python, Java, JavaScript, React, Docker, Kubernetes"
        ),
        pages=1,
    )
    pdf_path = tmp_path / "clean_resume.pdf"
    pdf_path.write_bytes(content)

    with PDFDocument(pdf_path) as pdf:
        yield pdf


@pytest.fixture
def scanned_pdf(tmp_path: Path) -> PDFDocument:
    """Create a PDF that simulates a scanned document.

    The text is embedded as an image, not as extractable text.
    This should fail the text_extraction checker.
    """
    content = create_scanned_pdf(
        text=(
            "Jane Smith\n"
            "Marketing Manager\n"
            "jane@example.com\n"
            "\n"
            "This is a scanned resume that ATS cannot read properly."
        ),
        pages=1,
    )
    pdf_path = tmp_path / "scanned_resume.pdf"
    pdf_path.write_bytes(content)

    with PDFDocument(pdf_path) as pdf:
        yield pdf


@pytest.fixture
def multicolumn_pdf(tmp_path: Path) -> PDFDocument:
    """Create a PDF with a two-column layout.

    This should trigger the layout checker's multi-column detection.
    """
    content = create_multicolumn_pdf(
        left_column_text=(
            "Left Column\nExperience\nCompany A - Role A\nDescription of work\nMore details here\n"
        )
        * 5,
        right_column_text=(
            "Right Column\nEducation\nUniversity Name\nDegree information\nAdditional details\n"
        )
        * 5,
        pages=1,
    )
    pdf_path = tmp_path / "multicolumn_resume.pdf"
    pdf_path.write_bytes(content)

    with PDFDocument(pdf_path) as pdf:
        yield pdf


@pytest.fixture
def empty_pdf(tmp_path: Path) -> PDFDocument:
    """Create a PDF with a single blank page.

    This should trigger warnings about empty/minimal content.
    """
    content = create_empty_pdf()
    pdf_path = tmp_path / "empty.pdf"
    pdf_path.write_bytes(content)

    with PDFDocument(pdf_path) as pdf:
        yield pdf


@pytest.fixture
def large_file_pdf(tmp_path: Path) -> PDFDocument:
    """Create a PDF that exceeds the file size warning threshold.

    Default config: warning at 500KB, critical at 1024KB.
    This fixture creates a ~600KB file to trigger warning.
    """
    content = create_large_pdf(target_size_kb=600)
    pdf_path = tmp_path / "large_file.pdf"
    pdf_path.write_bytes(content)

    with PDFDocument(pdf_path) as pdf:
        yield pdf


@pytest.fixture
def metadata_leak_pdf(tmp_path: Path) -> PDFDocument:
    """Create a PDF with metadata that reveals the creation software.

    This should trigger the metadata checker.
    """
    content = create_pdf_with_metadata(
        creator="Microsoft Word",
        producer="Microsoft Word to PDF Converter",
        title="Resume",
        author="Test User",
    )
    pdf_path = tmp_path / "metadata_leak.pdf"
    pdf_path.write_bytes(content)

    with PDFDocument(pdf_path) as pdf:
        yield pdf


@pytest.fixture
def special_chars_pdf(tmp_path: Path) -> PDFDocument:
    """Create a PDF containing various special Unicode characters.

    This should trigger the special_chars checker.
    """
    content = create_pdf_with_special_chars()
    pdf_path = tmp_path / "special_chars.pdf"
    pdf_path.write_bytes(content)

    with PDFDocument(pdf_path) as pdf:
        yield pdf


@pytest.fixture
def no_contact_pdf(tmp_path: Path) -> PDFDocument:
    """Create a PDF without contact information.

    This should trigger the contact_info checker.
    """
    content = create_test_pdf(
        text=(
            "Anonymous Candidate\n"
            "\n"
            "EXPERIENCE\n"
            "Worked at various companies\n"
            "\n"
            "SKILLS\n"
            "Various technical skills"
        ),
        pages=1,
    )
    pdf_path = tmp_path / "no_contact.pdf"
    pdf_path.write_bytes(content)

    with PDFDocument(pdf_path) as pdf:
        yield pdf


@pytest.fixture
def unusual_fonts_pdf(tmp_path: Path) -> PDFDocument:
    """Create a PDF using Courier (monospace) font.

    Courier is not in the default safe_fonts set, which may
    trigger the font checker depending on how normalization works.
    """
    content = create_test_pdf(
        text=(
            "Custom Font Resume\n"
            "Using monospace font throughout\n"
            "This may be flagged by font checker"
        ),
        pages=1,
        font_name="cour",
    )
    pdf_path = tmp_path / "unusual_fonts.pdf"
    pdf_path.write_bytes(content)

    with PDFDocument(pdf_path) as pdf:
        yield pdf


@pytest.fixture
def table_layout_pdf(tmp_path: Path) -> PDFDocument:
    """Create a PDF with table-like visual layout using drawn lines.

    This may trigger the layout checker's table detection.
    """
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)

    # Draw a simple table grid
    # Horizontal lines
    for y in [100, 130, 160, 190]:
        page.draw_line(fitz.Point(72, y), fitz.Point(523, y))
    # Vertical lines
    for x in [72, 200, 350, 523]:
        page.draw_line(fitz.Point(x, 100), fitz.Point(x, 190))

    # Add text in cells
    text_writer = fitz.TextWriter(page.rect)
    text_writer.append(
        (80, 125),
        "Skill",
        font=fitz.Font("helv"),
        fontsize=10,
    )
    text_writer.append(
        (210, 125),
        "Years",
        font=fitz.Font("helv"),
        fontsize=10,
    )
    text_writer.append(
        (360, 125),
        "Level",
        font=fitz.Font("helv"),
        fontsize=10,
    )
    text_writer.write_text(page)

    pdf_bytes = doc.tobytes()
    doc.close()

    pdf_path = tmp_path / "table_layout.pdf"
    pdf_path.write_bytes(pdf_bytes)

    with PDFDocument(pdf_path) as pdf:
        yield pdf


# =============================================================================
# Temporary File Fixtures
# =============================================================================


@pytest.fixture
def tmp_pdf_path(tmp_path: Path) -> Path:
    """Return a temporary file path for creating test PDFs.

    The file is NOT created by this fixture — use this when you need
    to create a PDF file manually in your test.
    """
    return tmp_path / "test_document.pdf"


# =============================================================================
# Utility Fixtures
# =============================================================================


@pytest.fixture
def severity_levels() -> list[Severity]:
    """Return all severity levels for parameterized tests."""
    return [Severity.CRITICAL, Severity.WARNING, Severity.OK]


@pytest.fixture
def checker_names() -> list[str]:
    """Return all registered checker names."""
    from ats_checker.checkers.registry import CheckerRegistry

    return [cls.name for cls in CheckerRegistry.get_all()]
