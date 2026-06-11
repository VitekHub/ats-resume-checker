from __future__ import annotations

from pathlib import Path

from .config import Config as Config
from .models import (
    BatchReport as BatchReport,
)
from .models import (
    CheckerResult as CheckerResult,
)
from .models import (
    CheckReport as CheckReport,
)
from .models import (
    Issue as Issue,
)
from .models import (
    Severity as Severity,
)

__version__ = "0.1.0"


def run_check(pdf_path: Path, config: Config | None = None) -> CheckReport:
    """
    Runs all ATS checks on the specified PDF file.

    Args:
        pdf_path: Path to the PDF resume/CV.
        config: Optional configuration override.

    Returns:
        A CheckReport containing the results of all performed checks.

    Raises:
        NotImplementedError: This function is implemented in Phase 2.
    """
    raise NotImplementedError(
        "run_check() is not yet implemented. See Phase 2 of the implementation plan."
    )
