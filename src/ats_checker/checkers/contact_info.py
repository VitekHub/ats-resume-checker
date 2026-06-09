from re import search

from ats_checker.checkers.base import BaseChecker
from ats_checker.checkers.registry import register_checker
from ats_checker.models import Issue, Severity
from ats_checker.pdf_utils import PDFDocument


@register_checker
class ContactInfoChecker(BaseChecker):
    """
    Detects presence of essential contact information (email and phone) in the resume.
    ATS parsers need these to correctly identify and contact the candidate.
    """

    name = "contact_info"
    description = "Detects email and phone number in the resume text"
    requires_text = True
    severity_on_fail = Severity.CRITICAL

    def check(self, pdf: PDFDocument) -> list[Issue]:
        text = pdf.text
        if not text:
            return [
                Issue(
                    severity=Severity.CRITICAL,
                    title="No text found",
                    detail="Could not extract any text from the PDF to check for contact info.",
                    checker_name=self.name,
                    location="Entire document",
                )
            ]

        patterns = self.config.sections.contact_patterns
        if not patterns:
            return []

        # Email is typically the first pattern
        has_email = bool(search(patterns[0], text))
        # Phone is any of the subsequent patterns
        has_phone = any(search(p, text) for p in patterns[1:])

        issues = []

        if not has_email:
            issues.append(
                Issue(
                    severity=Severity.CRITICAL,
                    title="No email address detected",
                    detail="ATS needs your email to contact you. Make sure it's plain text, "
                    "not in an image or special font.",
                    checker_name=self.name,
                    location="Entire document",
                )
            )

        if not has_phone:
            issues.append(
                Issue(
                    severity=Severity.WARNING,
                    title="No phone number detected",
                    detail="Consider adding a phone number in plain text format.",
                    checker_name=self.name,
                    location="Entire document",
                )
            )

        if has_email and has_phone:
            issues.append(
                Issue(
                    severity=Severity.OK,
                    title="Contact info found",
                    detail="Email and phone detected in readable text.",
                    checker_name=self.name,
                    location="Entire document",
                )
            )

        return issues
