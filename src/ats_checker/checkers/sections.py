from __future__ import annotations

from ats_checker.checkers.base import BaseChecker
from ats_checker.checkers.registry import register_checker
from ats_checker.models import Issue, Severity
from ats_checker.pdf_utils import PDFDocument, extract_text


@register_checker
class SectionsChecker(BaseChecker):
    """
    Checks for standard resume sections that ATS parsers expect.
    """

    name = "sections"
    description = "Checks for standard resume sections that ATS parsers expect"
    requires_text = True
    severity_on_fail = Severity.WARNING

    def check(self, pdf: PDFDocument) -> list[Issue]:
        """
        Analyzes the extracted text to find expected resume sections.
        """
        # 1. Extract and normalize text
        full_text = extract_text(pdf)
        text_lower = full_text.lower()

        # 2. Detect sections
        found_sections: list[str] = []
        missing_sections: list[str] = []

        expected_sections = self.config.sections.expected_sections

        for section, keywords in expected_sections.items():
            if any(kw.lower() in text_lower for kw in keywords):
                found_sections.append(section)
            else:
                missing_sections.append(section)

        # 3. Generate results
        if missing_sections:
            missing_list = ", ".join(missing_sections)
            return [
                Issue(
                    severity=self.severity_on_fail,
                    title="Missing common sections",
                    detail=(
                        f"Could not find: {missing_list}. ATS parsers rely on "
                        f"section headers to categorize your content. Use standard "
                        f"headers like Experience, Education, Skills."
                    ),
                    checker_name=self.name,
                    remediation="Use standard section headers like Experience, Education, Skills.",
                    location="Entire document",
                )
            ]

        # All expected sections were found
        found_list = ", ".join(found_sections)
        return [
            Issue(
                severity=Severity.OK,
                title="All key sections found",
                detail=f"Detected: {found_list}",
                checker_name=self.name,
                remediation="",
                location="Entire document",
            )
        ]
