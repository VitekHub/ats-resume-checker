from ats_checker.checkers.base import BaseChecker
from ats_checker.checkers.registry import register_checker
from ats_checker.models import Issue, Severity
from ats_checker.pdf_utils import PDFDocument, extract_images_info


@register_checker
class ImagesChecker(BaseChecker):
    name = "images"
    description = "Detects embedded images that ATS cannot read"
    requires_text = False

    def check(self, pdf: PDFDocument) -> list[Issue]:
        """
        Detects images in the PDF and classifies them as large or small.
        Returns a list of Issues based on the findings.
        """
        images = extract_images_info(pdf, self.config)

        if not images:
            return [
                Issue(
                    severity=Severity.OK,
                    title="No embedded images detected",
                    detail="The document is clean of potential image-based parsing barriers.",
                    remediation=None,
                    location="Entire file",
                    checker_name=self.name,
                )
            ]

        large_images = [img for img in images if img.is_large]
        small_images = [img for img in images if not img.is_large]

        issues: list[Issue] = []

        if large_images:
            pages = sorted(list({img.page + 1 for img in large_images}))
            location = f"Page(s): {', '.join(map(str, pages))}"
            issues.append(
                Issue(
                    severity=Severity.CRITICAL,
                    title="Large embedded image(s) detected",
                    detail="ATS may fail to parse the surrounding text or ignore the file.",
                    remediation="Remove portrait photos, large graphics, or scanned "
                    "elements. Convert to plain text if necessary.",
                    location=location,
                    checker_name=self.name,
                )
            )

        elif small_images:
            pages = sorted(list({img.page + 1 for img in small_images}))
            location = f"Page(s): {', '.join(map(str, pages))}"
            issues.append(
                Issue(
                    severity=Severity.WARNING,
                    title="Small embedded images/icons detected",
                    detail="While usually ignored, excessive use of symbols can sometimes "
                    "confuse simpler ATS parsers.",
                    remediation="Replace complex icons with standard bullet points or text labels.",
                    location=location,
                    checker_name=self.name,
                )
            )

        return issues
