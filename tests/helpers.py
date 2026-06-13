"""Test helpers for ATS Resume Checker.

Provides utilities for:
- Creating test PDFs programmatically using PyMuPDF
- Asserting Issue properties in tests
"""

from __future__ import annotations

from pathlib import Path

import fitz  # PyMuPDF

from ats_checker.models import Issue, Severity

# =============================================================================
# PDF Generation Helpers
# =============================================================================


def create_test_pdf(
    text: str = "John Doe\nSoftware Engineer\njohn@example.com",
    pages: int = 1,
    font_name: str = "helv",
    font_size: float = 12,
) -> bytes:
    """Create a simple text-based PDF in memory.

    Args:
        text: Text content to insert (newline-separated lines).
        pages: Number of pages to create.
        font_name: PyMuPDF built-in font name (e.g., "helv", "times", "cour").
        font_size: Font size in points.

    Returns:
        PDF file content as bytes.
    """
    doc = fitz.open()

    for _ in range(pages):
        page = doc.new_page(width=595, height=842)  # A4
        if text:
            text_writer = fitz.TextWriter(page.rect)
            text_writer.append(
                (72, 100),
                text,
                font=fitz.Font(font_name),
                fontsize=font_size,
            )
            text_writer.write_text(page)

    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


def create_scanned_pdf(
    text: str = "Scanned Resume Content",
    pages: int = 1,
) -> bytes:
    """Create a PDF that simulates a scanned document.

    The text is rendered as an image, not as extractable text.
    This should fail text extraction checks.

    Args:
        text: Text to render (will NOT be extractable by text tools).
        pages: Number of pages.

    Returns:
        PDF file content as bytes.
    """
    # Step 1: Create a temporary PDF with text
    temp_doc = fitz.open()
    for _ in range(pages):
        page = temp_doc.new_page(width=595, height=842)
        text_writer = fitz.TextWriter(page.rect)
        text_writer.append(
            (72, 100),
            text,
            font=fitz.Font("helv"),
            fontsize=12,
        )
        text_writer.write_text(page)

    # Step 2: Convert each page to an image and create image-only PDF
    scanned_doc = fitz.open()
    for page_num in range(temp_doc.page_count):
        page = temp_doc[page_num]
        mat = fitz.Matrix(2, 2)  # 2x zoom
        pix = page.get_pixmap(matrix=mat)

        new_page = scanned_doc.new_page(width=page.rect.width, height=page.rect.height)
        new_page.insert_image(new_page.rect, pixmap=pix)

    temp_doc.close()
    pdf_bytes = scanned_doc.tobytes()
    scanned_doc.close()
    return pdf_bytes


def create_multicolumn_pdf(
    left_column_text: str = "Left Column\n" * 10,
    right_column_text: str = "Right Column\n" * 10,
    pages: int = 1,
) -> bytes:
    """Create a PDF with a two-column layout.

    Args:
        left_column_text: Text for the left column.
        right_column_text: Text for the right column.
        pages: Number of pages.

    Returns:
        PDF file content as bytes.
    """
    doc = fitz.open()

    for _ in range(pages):
        page = doc.new_page(width=595, height=842)

        # Left column
        left_writer = fitz.TextWriter(page.rect)
        left_writer.append(
            (72, 100),
            left_column_text,
            font=fitz.Font("helv"),
            fontsize=10,
        )
        left_writer.write_text(page)

        # Right column
        right_writer = fitz.TextWriter(page.rect)
        right_writer.append(
            (315, 100),
            right_column_text,
            font=fitz.Font("helv"),
            fontsize=10,
        )
        right_writer.write_text(page)

    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


def create_empty_pdf() -> bytes:
    """Create a PDF with a single blank page (no text content).

    Returns:
        PDF file content as bytes.
    """
    doc = fitz.open()
    doc.new_page(width=595, height=842)  # A4 blank page
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


def create_pdf_with_metadata(
    creator: str | None = None,
    producer: str | None = None,
    title: str | None = None,
    author: str | None = None,
    subject: str | None = None,
    keywords: str | None = None,
) -> bytes:
    """Create a PDF with specific metadata values.

    Args:
        creator: Application that created the PDF.
        producer: PDF converter if different from creator.
        title: Document title.
        author: Document author.
        subject: Document subject.
        keywords: Keywords for searching.

    Returns:
        PDF file content as bytes.
    """
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)

    # Add minimal text so PDF is valid
    text_writer = fitz.TextWriter(page.rect)
    text_writer.append((72, 100), "Test Document", font=fitz.Font("helv"), fontsize=12)
    text_writer.write_text(page)

    # Set metadata
    metadata: dict[str, str] = {}
    if creator:
        metadata["creator"] = creator
    if producer:
        metadata["producer"] = producer
    if title:
        metadata["title"] = title
    if author:
        metadata["author"] = author
    if subject:
        metadata["subject"] = subject
    if keywords:
        metadata["keywords"] = keywords

    if metadata:
        doc.set_metadata(metadata)

    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


def create_large_pdf(
    target_size_kb: int = 600,
    text: str = "Sample resume content for size testing.\n" * 50,
) -> bytes:
    """Create a PDF that exceeds a specified size threshold.

    Achieves target size by adding pages with repeated content.

    Args:
        target_size_kb: Target file size in kilobytes.
        text: Base text content to repeat per page.

    Returns:
        PDF file content as bytes.
    """
    doc = fitz.open()

    while True:
        page = doc.new_page(width=595, height=842)
        text_writer = fitz.TextWriter(page.rect)
        y_pos = 100.0
        for _ in range(30):
            text_writer.append(
                (72, y_pos),
                text,
                font=fitz.Font("helv"),
                fontsize=10,
            )
            y_pos += 15

        text_writer.write_text(page)

        # Check current size
        current_bytes = doc.tobytes()
        if len(current_bytes) / 1024 >= target_size_kb:
            break

        # Safety limit to prevent infinite loops
        if doc.page_count > 100:
            break

    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


def create_pdf_with_special_chars() -> bytes:
    """Create a PDF containing various special Unicode characters.

    Includes: em dashes, en dashes, bullets, arrows, box-drawing chars,
    geometric shapes, and other problematic characters.

    Returns:
        PDF file content as bytes.
    """
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)

    special_text = (
        "Special Characters Test\n"
        "Em dash: — En dash: – Ellipsis: …\n"
        "Bullet: • Arrow: → Box: ┌─┐\n"
        "Geometric: ■ ▲ ● ★\n"
        "Symbols: © ® ™ € £ ¥\n"
        "Math: ≤ ≥ ≠ ± × ÷\n"
    )

    text_writer = fitz.TextWriter(page.rect)
    text_writer.append(
        (72, 100),
        special_text,
        font=fitz.Font("helv"),
        fontsize=12,
    )
    text_writer.write_text(page)

    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


def save_test_pdf(
    content: bytes,
    filename: str,
    directory: Path | str | None = None,
) -> Path:
    """Save PDF bytes to a file.

    Args:
        content: PDF file content as bytes.
        filename: Name for the file.
        directory: Directory to save to (default: tests/fixtures/).

    Returns:
        Path to the saved file.
    """
    if directory is None:
        directory = Path(__file__).parent / "fixtures"
    elif isinstance(directory, str):
        directory = Path(directory)

    directory.mkdir(parents=True, exist_ok=True)
    file_path = directory / filename
    file_path.write_bytes(content)
    return file_path


# =============================================================================
# Assertion Helpers
# =============================================================================


def assert_issue(
    issue: Issue,
    expected_severity: Severity | None = None,
    expected_title_contains: str | None = None,
    expected_checker: str | None = None,
    expected_detail_contains: str | None = None,
) -> None:
    """Assert that an Issue has expected properties.

    Args:
        issue: The Issue to validate.
        expected_severity: Expected severity level (or None to skip).
        expected_title_contains: Substring expected in title (or None).
        expected_checker: Expected checker_name (or None).
        expected_detail_contains: Substring expected in detail (or None).

    Raises:
        AssertionError: If any assertion fails.
    """
    if expected_severity is not None:
        assert issue.severity == expected_severity, (
            f"Expected severity {expected_severity}, got {issue.severity}"
        )

    if expected_title_contains is not None:
        assert expected_title_contains.lower() in issue.title.lower(), (
            f"Expected title to contain '{expected_title_contains}', got '{issue.title}'"
        )

    if expected_checker is not None:
        assert issue.checker_name == expected_checker, (
            f"Expected checker '{expected_checker}', got '{issue.checker_name}'"
        )

    if expected_detail_contains is not None:
        assert expected_detail_contains.lower() in issue.detail.lower(), (
            f"Expected detail to contain '{expected_detail_contains}', got '{issue.detail}'"
        )


def assert_issues_contains(
    issues: list[Issue],
    expected_severity: Severity | None = None,
    expected_title_contains: str | None = None,
    expected_count: int | None = None,
) -> None:
    """Assert that a list of issues contains expected issues.

    Args:
        issues: List of Issue objects to search.
        expected_severity: Filter by severity (or None to skip).
        expected_title_contains: Filter by title substring (or None).
        expected_count: Expected number of matching issues
            (None means >= 1).

    Raises:
        AssertionError: If assertions fail.
    """
    matching = issues

    if expected_severity is not None:
        matching = [i for i in matching if i.severity == expected_severity]

    if expected_title_contains is not None:
        matching = [i for i in matching if expected_title_contains.lower() in i.title.lower()]

    if expected_count is not None:
        assert len(matching) == expected_count, (
            f"Expected {expected_count} matching issues, got {len(matching)}"
        )
    else:
        assert len(matching) >= 1, f"Expected at least one matching issue, got {len(matching)}"
