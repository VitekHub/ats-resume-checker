from ats_checker.checkers.base import BaseChecker
from ats_checker.checkers.registry import register_checker
from ats_checker.models import Issue, Severity
from ats_checker.pdf_utils import PDFDocument


@register_checker
class FileSizeChecker(BaseChecker):
    """
    Checks PDF file size against common portal upload limits.
    """

    name = "file_size"
    description = "Checks PDF file size against common portal upload limits"
    requires_text = False
    severity_on_fail = Severity.WARNING

    def check(self, pdf: PDFDocument) -> list[Issue]:
        """
        Evaluate the PDF file size against configured thresholds.
        """
        size_kb = pdf.file_size_kb
        warning_kb = self.config.file_size.warning_kb
        critical_kb = self.config.file_size.critical_kb

        if size_kb > critical_kb:
            return [
                Issue(
                    severity=Severity.CRITICAL,
                    title="File too large",
                    detail=f"{size_kb:.0f} KB — many portals reject files over {critical_kb} KB",
                    checker_name=self.name,
                    remediation=(
                        "Compress the PDF or remove high-resolution images to reduce file size."
                    ),
                    location="Entire document",
                )
            ]
        elif size_kb > warning_kb:
            return [
                Issue(
                    severity=Severity.WARNING,
                    title="File approaching size limit",
                    detail=f"{size_kb:.0f} KB — some portals cap uploads at {warning_kb} KB",
                    checker_name=self.name,
                    remediation=(
                        "Consider optimizing the PDF size to ensure compatibility with all portals."
                    ),
                    location="Entire document",
                )
            ]

        return [
            Issue(
                severity=Severity.OK,
                title="File size is optimal",
                detail=f"{size_kb:.0f} KB — file size is within acceptable limits",
                checker_name=self.name,
                remediation=None,
                location="Entire document",
            )
        ]
