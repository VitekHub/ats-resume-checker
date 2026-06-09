import io
from pathlib import Path
from typing import Dict, List

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from ..config import Config
from ..models import CheckReport, Severity
from .base import BaseReporter, register_reporter

# Mapping from Severity to rich color and icon
_SEVERITY_CLR: Dict[Severity, str] = {
    Severity.CRITICAL: "red",
    Severity.WARNING: "yellow",
    Severity.OK: "green",
}

_SEVERITY_ICON: Dict[Severity, str] = {
    Severity.CRITICAL: "🔴",
    Severity.WARNING: "🟡",
    Severity.OK: "🟢",
}


@register_reporter
class TerminalReporter(BaseReporter):
    format_name = "terminal"

    def __init__(self) -> None:
        self._cfg = Config()
        # Main console for direct printing (report_to_console)
        self.console = Console(
            force_terminal=True,
            color_system="auto" if self._cfg.output.color_output else None,
        )

    def report(self, result: CheckReport, output: Path | None = None) -> str:
        """
        Generate a formatted Rich report as a string.
        """
        # Use a dedicated console with a StringIO buffer to capture the rendered text
        capture_console = Console(
            file=io.StringIO(),
            force_terminal=True,
            color_system="auto" if self._cfg.output.color_output else None,
            width=self.console.width,
        )

        # 1. Header Table
        header = Table.grid(padding=(0, 1))
        header.add_column(style="bold cyan")
        header.add_column()
        header.add_row("File:", result.pdf_path.name)
        header.add_row("Timestamp:", result.timestamp.strftime("%Y-%m-%d %H:%M:%S"))
        if result.score is not None:
            header.add_row("Score:", f"{result.score:.1f}%")

        capture_console.print(header)
        capture_console.print("\n")

        # 2. Issue Grouping and Rendering
        grouped: Dict[Severity, List] = {s: [] for s in Severity}
        for issue in result.all_issues:
            grouped[issue.severity].append(issue)

        # Filter OK issues if not verbose
        if not self._cfg.output.verbose:
            grouped.pop(Severity.OK, None)

        for sev in [Severity.CRITICAL, Severity.WARNING, Severity.OK]:
            issues = grouped.get(sev)
            if not issues:
                continue

            sev_title = Text(
                f"{_SEVERITY_ICON[sev]} {sev.value.title()} Issues",
                style=f"bold {_SEVERITY_CLR[sev]}",
            )
            capture_console.print(sev_title)

            sev_table = Table(
                show_header=True,
                header_style="bold",
                box=None,
                padding=(0, 2),
            )
            sev_table.add_column("Checker", style="cyan", width=20)
            sev_table.add_column("Issue", style="bold")
            sev_table.add_column("Detail", style="dim")
            sev_table.add_column("Location", style="magenta")
            sev_table.add_column("Remediation", style="italic")

            for i in issues:
                sev_table.add_row(
                    i.checker_name,
                    i.title,
                    i.detail,
                    i.location or "-",
                    i.remediation or "-",
                )

            capture_console.print(Panel(sev_table, border_style=_SEVERITY_CLR[sev]))
            capture_console.print("\n")

        # 3. Verdict Footer
        if result.critical_count > 0:
            verdict = "✗ NOT ATS-FRIENDLY"
            verdict_style = "bold red"
        elif result.warning_count > 0:
            verdict = "⚠ LIKELY ATS-COMPATIBLE"
            verdict_style = "bold yellow"
        else:
            verdict = "✓ ATS-FRIENDLY"
            verdict_style = "bold green"

        footer = Panel(Text(verdict, style=verdict_style), border_style=verdict_style, expand=False)
        capture_console.print(footer)

        full_report = capture_console.file.getvalue()

        # Write to file if output path is provided
        if output:
            output.write_text(full_report, encoding="utf-8")

        return full_report

    def report_to_console(self, result: CheckReport) -> None:
        """
        Print the report directly to the terminal.
        """
        # Instead of just printing the string from report(),
        # we use the actual console to maintain the best rendering
        # But since report() now returns the string, we can just use that.
        # To be safe and efficient, we call report and print the result.
        self.console.print(self.report(result))
