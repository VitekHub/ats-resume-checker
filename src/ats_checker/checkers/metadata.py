from __future__ import annotations

from ats_checker.checkers.base import BaseChecker
from ats_checker.checkers.registry import register_checker
from ats_checker.models import Issue, Severity
from ats_checker.pdf_utils import PDFDocument


@register_checker
class MetadataChecker(BaseChecker):
    """
    Checks PDF metadata for personal information leaks.

    This checker examines common metadata fields and flags any that contain
    information not identified as common software signatures.
    """

    name = "metadata"
    description = "Checks PDF metadata for personal information leaks"
    requires_text = False
    severity_on_fail = Severity.WARNING

    def check(self, pdf: PDFDocument) -> list[Issue]:
        """
        Analyze the PDF's metadata for potential personal information leaks.

        Args:
            pdf: The wrapped PDF document.

        Returns:
            A list containing a WARNING Issue if leaks are found, otherwise an OK Issue.
        """
        target_fields = ["author", "subject", "creator", "producer"]
        leaks: list[str] = []

        # Pre-calculate software keywords for efficient lookups
        software_keywords = {kw.lower() for kw in self.config.metadata.software_keywords}

        for field in target_fields:
            val = pdf.metadata.get(field)
            if val is None:
                continue

            val_str = str(val).strip()
            if not val_str:
                continue

            val_lower = val_str.lower()
            # If no software keywords match, consider it a personal info leak
            if not any(kw in val_lower for kw in software_keywords):
                leaks.append(f"{field}: {val_str}")

        if leaks:
            leak_details = ", ".join(leaks)
            return [
                Issue(
                    title="PDF metadata contains personal information",
                    detail=f"The following metadata fields may leak personal info: {leak_details}",
                    severity=self.severity_on_fail,
                    checker_name=self.name,
                    location="Document metadata",
                    remediation="Strip metadata in your PDF editor (File → Properties).",
                )
            ]

        return [
            Issue(
                title="PDF metadata is clean",
                detail="No personal information leaks detected in PDF metadata.",
                severity=Severity.OK,
                checker_name=self.name,
                location="Document metadata",
                remediation=None,
            )
        ]
