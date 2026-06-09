import html
from pathlib import Path
from typing import Final

from ..models import CheckReport, Issue, Severity
from .base import BaseReporter, register_reporter

# --- CSS Styles ---
CSS: Final[str] = """
body {
    font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI",
        Roboto, "Helvetica Neue", Arial, sans-serif;
    line-height: 1.6;
    color: #212529;
    max-width: 900px;
    margin: 0 auto;
    padding: 20px;
    background-color: #f8f9fa;
}
header {
    text-align: center;
    margin-bottom: 30px;
    padding-bottom: 20px;
    border-bottom: 2px solid #dee2e6;
}
header h1 {
    margin: 0;
    color: #212529;
    font-size: 2rem;
}
header .timestamp {
    color: #6c757d;
    font-size: 0.9rem;
}
.summary-container {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 1.5rem;
    margin-bottom: 30px;
}
.card {
    background: white;
    border-radius: 8px;
    padding: 1.5rem;
    box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    text-align: center;
}
.score-card {
    grid-column: 1 / -1;
    background: #212529;
    color: white;
}
.score-value {
    font-size: 3rem;
    font-weight: bold;
    display: block;
}
.score-label {
    font-size: 1.2rem;
    opacity: 0.9;
}
.summary-item .label {
    display: block;
    font-size: 0.9rem;
    color: #6c757d;
    text-transform: uppercase;
    margin-bottom: 0.5rem;
}
.summary-item .value {
    font-size: 2rem;
    font-weight: bold;
}
.critical-text { color: #dc3545; }
.warning-text { color: #ffc107; }
.ok-text { color: #28a745; }

.section {
    margin-bottom: 40px;
}
.section-title {
    font-size: 1.5rem;
    font-weight: bold;
    margin-bottom: 20px;
    padding-bottom: 10px;
    border-bottom: 3px solid #dee2e6;
}
.section-critical .section-title { color: #dc3545; border-bottom-color: #dc3545; }
.section-warning .section-title { color: #ffc107; border-bottom-color: #ffc107; }
.section-ok .section-title { color: #28a745; border-bottom-color: #28a745; }

.issue-card {
    background: white;
    border-left: 5px solid #dee2e6;
    margin-bottom: 15px;
    padding: 1.5rem;
    border-radius: 0 8px 8px 0;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05);
}
.severity-critical { border-left-color: #dc3545; }
.severity-warning { border-left-color: #ffc107; }
.severity-ok { border-left-color: #28a745; }

.issue-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 10px;
}
.issue-title {
    font-weight: bold;
    font-size: 1.2rem;
}
.badge {
    font-size: 0.75rem;
    background: #e9ecef;
    color: #495057;
    padding: 4px 8px;
    border-radius: 4px;
    font-weight: 500;
}
.issue-detail {
    color: #495057;
    margin-bottom: 15px;
}
.remediation {
    font-style: italic;
    background: #f1f3f5;
    padding: 10px 15px;
    border-radius: 6px;
    font-size: 0.95rem;
    color: #495057;
    border: 1px solid #dee2e6;
}
.remediation strong {
    color: #212529;
    font-style: normal;
}
footer {
    text-align: center;
    font-size: 0.85rem;
    color: #adb5bd;
    margin-top: 60px;
    padding-top: 20px;
    border-top: 1px solid #dee2e6;
}
@media (max-width: 600px) {
    .summary-container {
        grid-template-columns: 1fr;
    }
}
@media print {
    body { background-color: white; padding: 0; }
    .card, .issue-card { box-shadow: none; border: 1px solid #dee2e6; }
    .no-print { display: none; }
}
"""

# --- HTML Template ---
HTML_TEMPLATE: Final[str] = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ATS Resume Report - {{filename}}</title>
    <style>
        {css}
    </style>
</head>
<body>
    <header>
        <h1>ATS Resume Compatibility Report</h1>
        <div class="timestamp">Generated on: {{timestamp}}</div>
        <div class="timestamp">File: {{filename}}</div>
    </header>

    <main>
        <div class="summary-container">
            <div class="card score-card">
                <span class="score-label">Overall ATS Score</span>
                <span class="score-value">{{score}}%</span>
            </div>
            <div class="card summary-item">
                <span class="label">Critical Issues</span>
                <span class="value critical-text">{{critical_count}}</span>
            </div>
            <div class="card summary-item">
                <span class="label">Warnings</span>
                <span class="value warning-text">{{warning_count}}</span>
            </div>
            <div class="card summary-item">
                <span class="label">OK Checks</span>
                <span class="value ok-text">{{ok_count}}</span>
            </div>
        </div>

        <section class="section section-critical">
            <div class="section-title">🔴 Critical Issues</div>
            {{critical_issues}}
        </section>

        <section class="section section-warning">
            <div class="section-title">🟡 Warnings</div>
            {{warning_issues}}
        </section>

        <section class="section section-ok">
            <div class="section-title">🟢 Pass Checks</div>
            {{ok_issues}}
        </section>
    </main>

    <footer>
        Exported from ATS Resume Checker v0.1.0
    </footer>
</body>
</html>
"""


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
        severity_class = f"severity-{issue.severity.value}"

        return f"""
        <div class="issue-card {severity_class}">
            <div class="issue-header">
                <span class="issue-title">{self._escape(issue.title)}</span>
                <span class="badge">{self._escape(issue.location)}</span>
            </div>
            <div class="issue-detail">{self._escape(issue.detail)}</div>
            <div class="remediation">
                <strong>Fix:</strong> {self._escape(issue.remediation)}
            </div>
        </div>
        """

    def _render_section(self, result: CheckReport, severity: Severity) -> str:
        """Render a collection of issues for a specific severity."""
        issues = [i for i in result.all_issues if i.severity == severity]
        if not issues:
            return (
                '<p style="color: #6c757d; font-style: italic;">'
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
        report_html = HTML_TEMPLATE.replace("{{css}}", CSS)
        report_html = report_html.replace("{{filename}}", self._escape(result.pdf_path.name))

        # Convert datetime to string before escaping
        if hasattr(result.timestamp, "strftime"):
            ts_str = result.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        else:
            ts_str = str(result.timestamp)
        report_html = report_html.replace("{{timestamp}}", self._escape(ts_str))

        report_html = report_html.replace("{{score}}", f"{result.score:.1f}")
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
