import html
from pathlib import Path

from ..models import BatchReport, CheckReport, Issue, Severity
from .base import BaseReporter, register_reporter


# --- HTML Template ---
def _get_template(name: str = "report.html") -> str:
    """Load an HTML template from the filesystem."""
    template_path = Path(__file__).parent / "templates" / name
    return template_path.read_text(encoding="utf-8")


@register_reporter
class HTMLReporter(BaseReporter):
    """
    Reporter that produces a professional, self-contained HTML report of the ATS check results.
    """

    format_name = "html"

    def _escape(self, text: str | None) -> str:
        """Escape HTML special characters to prevent XSS."""
        return html.escape(text) if text else ""

    def _render_issue(self, issue: Issue) -> str:
        """Render a single issue as an HTML card."""
        # Map severity to Tailwind colors
        severity_map = {
            Severity.CRITICAL: {
                "bg": "bg-red-50",
                "border": "border-red-200",
                "text": "text-red-800",
                "accent": "bg-red-500",
                "remediation_bg": "bg-red-100/50",
            },
            Severity.WARNING: {
                "bg": "bg-amber-50",
                "border": "border-amber-200",
                "text": "text-amber-800",
                "accent": "bg-amber-500",
                "remediation_bg": "bg-amber-100/50",
            },
            Severity.OK: {
                "bg": "bg-emerald-50",
                "border": "border-emerald-200",
                "text": "text-emerald-800",
                "accent": "bg-emerald-500",
                "remediation_bg": "bg-emerald-100/50",
            },
        }

        style = severity_map.get(issue.severity, severity_map[Severity.OK])

        remediation_html = ""
        if issue.remediation:
            remediation_tpl = _get_template("remediation.html")
            remediation_html = (
                remediation_tpl.replace("{{remediation_bg}}", style["remediation_bg"])
                .replace("{{text}}", style["text"])
                .replace("{{remediation}}", self._escape(issue.remediation))
            )

        card_tpl = _get_template("issue_card.html")
        return (
            card_tpl.replace("{{border}}", style["border"])
            .replace("{{bg}}", style["bg"])
            .replace("{{text}}", style["text"])
            .replace("{{title}}", self._escape(issue.title))
            .replace("{{location}}", self._escape(issue.location))
            .replace("{{detail}}", self._escape(issue.detail))
            .replace("{{remediation_html}}", remediation_html)
        )

    def _render_section(self, result: CheckReport, severity: Severity) -> str:
        """Render a collection of issues for a specific severity."""
        issues = [i for i in result.all_issues if i.severity == severity]
        if not issues:
            return (
                '<p class="text-slate-400 italic text-sm py-4 px-2">'
                "No issues found in this category.</p>"
            )

        return "\n".join(self._render_issue(i) for i in issues)

    def report(self, result: CheckReport, output: Path | None = None) -> str:
        """
        Generate an HTML report from check results.

        Args:
            result: The check report to render.
            output: Optional path to write the HTML output to.

        Returns:
            The complete HTML report as a string.
        """
        # Render sections
        critical_html = self._render_section(result, Severity.CRITICAL)
        warning_html = self._render_section(result, Severity.WARNING)
        ok_html = self._render_section(result, Severity.OK)

        # Populate template
        report_html = _get_template()
        report_html = report_html.replace("{{filename}}", self._escape(result.pdf_path.name))

        # Convert datetime to string before escaping
        if hasattr(result.timestamp, "strftime"):
            ts_str = result.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        else:
            ts_str = str(result.timestamp)
        report_html = report_html.replace("{{timestamp}}", self._escape(ts_str))

        score_str = f"{result.score:.1f}%" if result.score is not None else "N/A"
        report_html = report_html.replace("{{score}}", score_str)
        report_html = report_html.replace("{{critical_count}}", str(result.critical_count))
        report_html = report_html.replace("{{warning_count}}", str(result.warning_count))
        report_html = report_html.replace("{{ok_count}}", str(result.ok_count))
        report_html = report_html.replace("{{critical_issues}}", critical_html)
        report_html = report_html.replace("{{warning_issues}}", warning_html)
        report_html = report_html.replace("{{ok_issues}}", ok_html)

        # Write to file if path provided
        if output:
            output.write_text(report_html, encoding="utf-8")

        return report_html

    def _render_file_section(self, result: CheckReport) -> str:
        """
        Render the HTML body for a single file's report section.

        Used by both single-file and batch HTML reports.
        """
        critical_html = self._render_section(result, Severity.CRITICAL)
        warning_html = self._render_section(result, Severity.WARNING)
        ok_html = self._render_section(result, Severity.OK)

        score_str = f"{result.score:.1f}%" if result.score is not None else "N/A"
        ts_str = (
            result.timestamp.strftime("%Y-%m-%d %H:%M:%S")
            if hasattr(result.timestamp, "strftime")
            else str(result.timestamp)
        )

        section_tpl = _get_template("file_section.html")
        return (
            section_tpl.replace("{{filename}}", self._escape(result.pdf_path.name))
            .replace("{{timestamp}}", self._escape(ts_str))
            .replace("{{score}}", score_str)
            .replace("{{critical_count}}", str(result.critical_count))
            .replace("{{warning_count}}", str(result.warning_count))
            .replace("{{ok_count}}", str(result.ok_count))
            .replace("{{critical_issues}}", critical_html)
            .replace("{{warning_issues}}", warning_html)
            .replace("{{ok_issues}}", ok_html)
        )

    def report_batch(self, batch: BatchReport, output: Path | None = None) -> str:
        """
        Generate an HTML batch report from multiple check results.

        Args:
            batch: The BatchReport containing multiple CheckReports.
            output: Optional path to write the HTML output to.

        Returns:
            The complete HTML batch report as a string.
        """
        file_sections = "\n".join(self._render_file_section(r) for r in batch.reports)

        ts_str = (
            batch.timestamp.strftime("%Y-%m-%d %H:%M:%S")
            if hasattr(batch.timestamp, "strftime")
            else str(batch.timestamp)
        )

        template = _get_template("batch_report.html")
        html = (
            template.replace("{{timestamp}}", self._escape(ts_str))
            .replace("{{total_files}}", str(batch.total_files))
            .replace("{{files_with_critical}}", str(batch.files_with_critical))
            .replace("{{files_with_warnings}}", str(batch.files_with_warnings))
            .replace("{{files_passed}}", str(batch.files_passed))
            .replace("{{file_sections}}", file_sections)
        )

        if output:
            output.write_text(html, encoding="utf-8")

        return html
