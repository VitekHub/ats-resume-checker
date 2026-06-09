from __future__ import annotations

from ats_checker.checkers.base import BaseChecker
from ats_checker.checkers.registry import register_checker
from ats_checker.models import Issue, Severity
from ats_checker.pdf_utils import PDFDocument, extract_text


@register_checker
class TextExtractionChecker(BaseChecker):
    """
    Verifies that text can be cleanly extracted from the PDF in reading order.
    Low alphabetic ratio or very short text length usually indicates a scanned PDF
    or garbled extraction, which is problematic for ATS.
    """

    name = "text_extraction"
    description = "Verifies text can be cleanly extracted in reading order"
    requires_text = True
    severity_on_fail = Severity.CRITICAL

    def check(self, pdf: PDFDocument) -> list[Issue]:
        """
        Run the text extraction quality check.
        """
        all_text = extract_text(pdf)
        stripped_text = all_text.strip()
        text_length = len(stripped_text)

        # 1. Length check
        if text_length < self.config.text.min_length_critical:
            return [
                Issue(
                    title="Almost no extractable text",
                    detail=(
                        f"Extracted text length ({text_length} chars) is below the "
                        f"minimum threshold ({self.config.text.min_length_critical} chars)."
                    ),
                    severity=Severity.CRITICAL,
                    checker_name=self.name,
                    location="Entire document",
                    remediation=(
                        "Ensure your resume is not a scanned image or a PDF created from a "
                        "picture. Use a text-based PDF exported from Word, Google Docs, or LaTeX."
                    ),
                )
            ]

        # 2. Alpha ratio check
        alpha_count = sum(1 for c in all_text if c.isalpha())
        alpha_ratio = alpha_count / max(text_length, 1)

        if alpha_ratio < self.config.text.alpha_ratio_critical:
            return [
                Issue(
                    title="Text appears garbled",
                    detail=(
                        f"The ratio of alphabetic characters ({alpha_ratio:.2%}) "
                        f"is below the critical threshold "
                        f"({self.config.text.alpha_ratio_critical:.2%})."
                    ),
                    severity=Severity.CRITICAL,
                    checker_name=self.name,
                    location="Entire document",
                    remediation=(
                        "Your PDF may be using non-standard encoding or is a poor OCR result. "
                        "Try re-saving the PDF with standard fonts and 'Embed Fonts' enabled."
                    ),
                )
            ]

        if alpha_ratio < self.config.text.alpha_ratio_warning:
            return [
                Issue(
                    title="Text may have extraction issues",
                    detail=(
                        f"The ratio of alphabetic characters ({alpha_ratio:.2%}) "
                        f"is below the warning threshold "
                        f"({self.config.text.alpha_ratio_warning:.2%})."
                    ),
                    severity=Severity.WARNING,
                    checker_name=self.name,
                    location="Entire document",
                    remediation=(
                        "Some characters might not be parsed correctly by ATS. "
                        "Avoid using complex symbols or non-standard character sets."
                    ),
                )
            ]

        # 3. OK case
        return [
            Issue(
                title="Text extracts cleanly",
                detail=(
                    "The PDF contains a healthy amount of extractable text with a high "
                    "alphabetic ratio."
                ),
                severity=Severity.OK,
                checker_name=self.name,
                location="Entire document",
                remediation=None,
            )
        ]
