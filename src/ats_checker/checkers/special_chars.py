from ats_checker.checkers.base import BaseChecker
from ats_checker.checkers.registry import register_checker
from ats_checker.models import Issue, Severity
from ats_checker.pdf_utils import PDFDocument


@register_checker
class SpecialCharsChecker(BaseChecker):
    """
    Flags unusual Unicode characters that may not parse correctly in ATS.
    """

    name = "special_chars"
    description = "Flags unusual Unicode characters that may not parse in ATS"
    requires_text = True
    severity_on_fail = Severity.WARNING

    def check(self, pdf: PDFDocument) -> list[Issue]:
        """
        Scan the extracted text for characters in problematic Unicode ranges.

        Args:
            pdf: The PDF document containing the extracted text.

        Returns:
            A list of issues if problematic characters are found, otherwise an OK issue.
        """
        text = pdf.text
        if not text:
            return [
                Issue(
                    severity=Severity.OK,
                    title="No text to analyze",
                    detail="No text was extracted from the PDF, skipping special character check.",
                    checker_name=self.name,
                )
            ]

        found_chars: dict[str, list[str]] = {}
        ranges = self.config.unicode.problematic_ranges

        for char in text:
            cp = ord(char)
            for start, end, name in ranges:
                if start <= cp <= end:
                    if name not in found_chars:
                        found_chars[name] = []
                    if len(found_chars[name]) < 5:
                        if char not in found_chars[name]:
                            found_chars[name].append(char)

        if found_chars:
            details = []
            for name, chars in found_chars.items():
                char_display = ", ".join(f"'{c}' (U+{ord(c):04X})" for c in chars)
                details.append(f"{name}: {char_display}")

            return [
                Issue(
                    severity=Severity.WARNING,
                    title="Special characters detected",
                    detail=(
                        f"Found: {'; '.join(details)}. Some ATS may not render these correctly."
                    ),
                    checker_name=self.name,
                    remediation=(
                        "Replace Unicode symbols with plain ASCII equivalents "
                        "(use - instead of —, * instead of •)."
                    ),
                    location="Entire document",
                )
            ]

        return [
            Issue(
                severity=Severity.OK,
                title="Characters are ATS-friendly",
                detail="No unusual Unicode characters detected.",
                checker_name=self.name,
                location="Entire document",
            )
        ]
