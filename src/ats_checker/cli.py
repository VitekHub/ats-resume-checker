from pathlib import Path
from typing import List, Optional

import typer
from rich.console import Console
from rich.progress import BarColumn, Progress, SpinnerColumn, TaskProgressColumn, TextColumn

from ats_checker.checkers.registry import CheckerRegistry
from ats_checker.config import Config
from ats_checker.engine import run_check
from ats_checker.models import CheckReport, Severity
from ats_checker.reporters import get_reporter
from ats_checker.reporters.utils import save_extracted_text

console = Console()
app = typer.Typer(
    name="ats-check",
    help="Check PDF resumes for ATS compatibility issues",
    rich_markup_mode="markdown",
)


def validate_checkers(checkers: Optional[List[str]], skip_checkers: Optional[List[str]]) -> None:
    """Validate that requested and skipped checkers exist in the registry."""
    valid_names = {cls.name for cls in CheckerRegistry.get_all()}

    if checkers:
        for name in checkers:
            if name not in valid_names:
                raise typer.BadParameter(
                    f"Unknown checker: {name!r}. Available: {', '.join(sorted(valid_names))}"
                )

    if skip_checkers:
        for name in skip_checkers:
            if name not in valid_names:
                raise typer.BadParameter(
                    f"Unknown checker to skip: {name!r}. "
                    f"Available: {', '.join(sorted(valid_names))}"
                )


@app.command()
def check(
    paths: List[Path] = typer.Argument(..., exists=True, help="PDF file(s) to check"),
    format: str = typer.Option(
        "terminal", "--format", "-f", help="Output format: terminal, json, html"
    ),
    output: Optional[Path] = typer.Option(
        None, "--output", "-o", help="Output file path (required for json/html format)"
    ),
    checker: Optional[List[str]] = typer.Option(
        None, "--checker", "-c", help="Run only these checkers (by name)"
    ),
    skip_checker: Optional[List[str]] = typer.Option(
        None, "--skip-checker", "-s", help="Skip these checkers (by name)"
    ),
    config_file: Optional[Path] = typer.Option(None, "--config", help="Path to configuration file"),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Show all checks including passing ones"
    ),
    no_color: bool = typer.Option(False, "--no-color", help="Disable colored output"),
    save_text: bool = typer.Option(
        False, "--save-text", help="Save extracted text as .extracted.txt sidecar file"
    ),
    score: bool = typer.Option(False, "--score", help="Calculate and show ATS compatibility score"),
) -> None:
    """
    Analyze PDF resumes for ATS compatibility issues.
    """
    # 1. Input Validation
    for path in paths:
        if path.suffix.lower() != ".pdf":
            console.print(f"[red]Error:[/red] File [bold]{path.name}[/bold] is not a PDF.")
            raise typer.Exit(code=2)

    if format in ("json", "html") and output is None and len(paths) > 1:
        console.print(
            f"[red]Error:[/red] Output path is required for [bold]{format}[/bold] "
            "format when checking multiple files."
        )
        raise typer.Exit(code=2)

    validate_checkers(checker, skip_checker)

    # 2. Config Loading
    config = Config()
    if config_file:
        config = config.load_from_file(config_file)

    # Override config with CLI options
    config.output.format = format
    config.output.color_output = not no_color
    config.output.verbose = verbose

    # 3. Execution
    reports: List[CheckReport] = []
    has_critical = False

    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console,
        ) as progress:
            task = progress.add_task("[cyan]Analyzing resumes...", total=len(paths))

            for path in paths:
                progress.update(task, description=f"[cyan]Checking {path.name}...")

                report = run_check(
                    pdf_path=path,
                    config=config,
                    checkers=checker,
                    skip_checkers=skip_checker,
                )

                if save_text:
                    save_extracted_text(report, path)

                # Check for critical issues to determine exit code
                if any(
                    issue.severity == Severity.CRITICAL
                    for result in report.check_results
                    for issue in result.issues
                ):
                    has_critical = True

                reports.append(report)
                progress.advance(task)

    except KeyboardInterrupt:
        console.print("\n[yellow]Aborted.[/yellow]")
        raise typer.Exit(code=2)

    # 4. Reporting
    try:
        reporter = get_reporter(format)
    except ValueError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(code=2)

    for report in reports:
        if format == "terminal":
            reporter.report_to_console(report)
        else:
            # For non-terminal, output is handled by reporter.report()
            # In batch mode with a single output path, this might overwrite.
            # Phase 4.4 will improve this.
            reporter.report(report, output=output)

    # 5. Exit
    if has_critical:
        raise typer.Exit(code=1)
    raise typer.Exit(code=0)


if __name__ == "__main__":
    app()
