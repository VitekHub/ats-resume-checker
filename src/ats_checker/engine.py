import logging
import time
from pathlib import Path
from typing import List, Optional, Type

from ats_checker.checkers.base import BaseChecker
from ats_checker.checkers.registry import CheckerRegistry
from ats_checker.config import Config
from ats_checker.models import CheckerResult, CheckReport, Issue, Severity
from ats_checker.pdf_utils import PDFDocument, extract_text
from ats_checker.reporters.utils import save_extracted_text

logger = logging.getLogger(__name__)


def run_check(
    pdf_path: Path,
    config: Optional[Config] = None,
    checkers: Optional[List[str]] = None,
    skip_checkers: Optional[List[str]] = None,
) -> CheckReport:
    """
    Orchestrates the execution of ATS checkers against a PDF resume.

    Args:
        pdf_path: Path to the PDF file to analyze.
        config: Configuration object. If None, default config is used.
        checkers: List of checker names to run. If None, all default checkers are used.
        skip_checkers: List of checker names to exclude from the run.

    Returns:
        A CheckReport containing the results of all executed checkers.
    """
    config = config or Config()

    # 1. Resolve which checkers to run
    resolved_checker_classes: List[Type[BaseChecker]] = []

    if checkers:
        for name in checkers:
            try:
                resolved_checker_classes.append(CheckerRegistry.get(name))
            except KeyError:
                logger.warning(f"Checker '{name}' not found in registry. Skipping.")
    else:
        resolved_checker_classes = CheckerRegistry.get_default()

    # Filter out skipped checkers
    if skip_checkers:
        skip_set = set(skip_checkers)
        resolved_checker_classes = [
            cls for cls in resolved_checker_classes if cls.name not in skip_set
        ]

    # 2. Execute checks within PDF document context
    results: List[CheckerResult] = []
    all_text: str | None = None

    with PDFDocument(pdf_path) as pdf:
        # Pre-load text if any selected checker requires it
        if any(cls.requires_text for cls in resolved_checker_classes):
            all_text = extract_text(pdf)

        for checker_class in resolved_checker_classes:
            checker_name = checker_class.name
            start_time = time.perf_counter()

            try:
                # Instantiate the checker and run its logic
                checker = checker_class(config)
                issues = checker.check(pdf)

            except Exception as e:
                logger.exception(f"Checker '{checker_name}' failed unexpectedly: {e}")
                # Record the failure as a CRITICAL issue
                issues = [
                    Issue(
                        severity=Severity.CRITICAL,
                        title=f"Checker Failure: {checker_name}",
                        detail=f"An unexpected error occurred while running the checker: {str(e)}",
                        checker_name=checker_name,
                        remediation="Internal tool error. Please report it to the developers.",
                        location="Engine",
                    )
                ]

            elapsed_ms = (time.perf_counter() - start_time) * 1000

            results.append(
                CheckerResult(
                    checker_name=checker_name, issues=issues, execution_time_ms=elapsed_ms
                )
            )

    # 3. Assemble the final report
    report = CheckReport(
        pdf_path=pdf_path,
        check_results=results,
        all_text=all_text,
        score=None,  # Scoring implemented in Phase 7
    )

    # Save extracted text as sidecar file
    save_extracted_text(report, pdf_path)

    return report
