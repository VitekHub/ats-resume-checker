from ats_checker.checkers.base import BaseChecker
from ats_checker.checkers.registry import register_checker
from ats_checker.models import Issue, Severity
from ats_checker.pdf_utils import PDFDocument, extract_font_info


@register_checker
class FontsChecker(BaseChecker):
    """
    Checks for non-standard or symbol fonts that ATS may not render correctly.
    """

    name = "fonts"
    description = "Checks for non-standard or symbol fonts that ATS may not render"
    requires_text = False
    severity_on_fail = Severity.WARNING

    def check(self, pdf: PDFDocument) -> list[Issue]:
        """
        Analyze fonts used in the PDF and flag any that are not recognized as safe.
        """
        fonts = extract_font_info(pdf)
        if not fonts:
            return [
                Issue(
                    severity=Severity.OK,
                    title="No fonts detected",
                    detail="No fonts were extracted from the document.",
                    checker_name=self.name,
                    remediation=None,
                    location="Entire document",
                )
            ]

        symbol_fonts_found = fonts.intersection(self.config.fonts.symbol_fonts)
        safe_fonts = self.config.fonts.safe_fonts
        unusual_fonts_found = {
            f
            for f in fonts
            if not any(f.startswith(sf) for sf in safe_fonts) and f not in symbol_fonts_found
        }

        issues: list[Issue] = []

        if symbol_fonts_found:
            issues.append(
                Issue(
                    severity=Severity.CRITICAL,
                    title="Symbol fonts detected",
                    detail=(
                        f"Detected symbol fonts: {', '.join(sorted(symbol_fonts_found))}. "
                        "These are often unreadable by ATS parsers."
                    ),
                    checker_name=self.name,
                    remediation="Use standard fonts like Arial, Calibri, or Helvetica.",
                    location="Entire document",
                )
            )

        if unusual_fonts_found:
            issues.append(
                Issue(
                    severity=Severity.WARNING,
                    title="Unusual fonts detected",
                    detail=(
                        f"Found {len(unusual_fonts_found)} unusual font(s): "
                        f"{', '.join(sorted(unusual_fonts_found))}. "
                        "Non-standard fonts may be misread by some ATS systems."
                    ),
                    checker_name=self.name,
                    remediation="Use standard fonts like Arial, Calibri, or Helvetica.",
                    location="Entire document",
                )
            )

        if not issues:
            issues.append(
                Issue(
                    severity=Severity.OK,
                    title="Fonts are standard",
                    detail="All detected fonts are recognized as ATS-safe.",
                    checker_name=self.name,
                    remediation=None,
                    location="Entire document",
                )
            )

        return issues
