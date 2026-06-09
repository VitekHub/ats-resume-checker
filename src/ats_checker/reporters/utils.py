from pathlib import Path

from ats_checker.models import CheckReport


def save_extracted_text(result: CheckReport, pdf_path: Path) -> Path | None:
    """
    Writes the extracted text from the report to a sidecar file.

    Args:
        result: The check report containing the extracted text.
        pdf_path: The path to the original PDF file.

    Returns:
        The path to the created sidecar file, or None if no text was available.
    """
    if result.all_text is None:
        return None

    text_file = pdf_path.with_suffix(".extracted.txt")
    text_file.write_text(result.all_text, encoding="utf-8")
    return text_file
