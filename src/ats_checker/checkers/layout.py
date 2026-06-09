from __future__ import annotations

from ats_checker.checkers.base import BaseChecker
from ats_checker.checkers.registry import register_checker
from ats_checker.models import Issue, Severity
from ats_checker.pdf_utils import PDFDocument


@register_checker
class LayoutChecker(BaseChecker):
    """
    Detects multi-column layouts and tables that scramble ATS text order.
    """

    name = "layout"
    description = "Detects multi-column layouts and tables that scramble ATS text order"
    requires_text = True
    severity_on_fail = Severity.WARNING

    def check(self, pdf: PDFDocument) -> list[Issue]:
        """
        Analyzes the PDF for tables and multi-column layouts.
        """
        issues: list[Issue] = []

        # Access the underlying pdfplumber document
        doc = pdf._pdfplumber_doc
        if doc is None:
            return [
                Issue(
                    severity=Severity.CRITICAL,
                    title="PDF Document Error",
                    detail="Unable to access PDF structure for layout analysis.",
                    checker_name=self.name,
                    remediation="Ensure the PDF is not corrupted or password-protected.",
                    location="Entire file",
                )
            ]

        for page_num, page in enumerate(doc.pages):
            location = f"Page {page_num + 1}"

            # 1. Table Detection
            tables = page.find_tables()
            if tables:
                issues.append(
                    Issue(
                        severity=self.severity_on_fail,
                        title="Table layout detected",
                        detail=(
                            f"{location}: found {len(tables)} table(s). "
                            "ATS often reads table cells in wrong order. "
                            "Prefer simple section headers with bullet points."
                        ),
                        checker_name=self.name,
                        remediation=(
                            "Use single-column layout. Replace tables with "
                            "section headers and bullet points."
                        ),
                        location=location,
                    )
                )

            # 2. Multi-column Detection
            words = page.extract_words()
            if len(words) >= self.config.layout.min_words_for_column_check:
                # Get unique sorted X positions
                x_positions = sorted(set(round(w["x0"], 0) for w in words))

                if len(x_positions) > 2:
                    # Calculate gaps between consecutive X positions
                    gaps = [
                        (x_positions[i + 1] - x_positions[i], i)
                        for i in range(len(x_positions) - 1)
                    ]

                    # Find the largest gap
                    if gaps:
                        max_gap, _ = max(gaps)
                        if max_gap > self.config.layout.column_gap_threshold:
                            issues.append(
                                Issue(
                                    severity=self.severity_on_fail,
                                    title="Multi-column layout suspected",
                                    detail=(
                                        f"{location}: text appears in multiple columns. "
                                        "ATS reads left-to-right, top-to-bottom — "
                                        "column text may get interleaved and jumbled."
                                    ),
                                    checker_name=self.name,
                                    remediation=(
                                        "Use single-column layout. Replace tables with "
                                        "section headers and bullet points."
                                    ),
                                    location=location,
                                )
                            )

        # 3. Success Case
        if not issues:
            issues.append(
                Issue(
                    severity=Severity.OK,
                    title="Single-column layout detected",
                    detail="Text appears in a single column — ATS will read it in order.",
                    checker_name=self.name,
                    remediation="",
                    location="Entire file",
                )
            )

        return issues
