from __future__ import annotations

from datetime import datetime
from enum import Enum
from pathlib import Path

from pydantic import BaseModel, Field, computed_field, field_validator


class Severity(str, Enum):
    """Severity level of an ATS compatibility issue."""

    CRITICAL = "critical"
    WARNING = "warning"
    OK = "ok"


class Issue(BaseModel):
    """
    Represents a single issue found by an ATS checker.
    """

    severity: Severity
    title: str
    detail: str
    checker_name: str
    remediation: str | None = Field(default=None, description="Suggested fix for the issue")
    location: str | None = Field(
        default=None, description="Where the issue was found (e.g., 'Page 1')"
    )

    @field_validator("title", "detail")
    @classmethod
    def must_not_be_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Field must not be empty or whitespace")
        return v

    def __repr__(self) -> str:
        return f"Issue(severity={self.severity.value}, title={self.title!r})"


class CheckerResult(BaseModel):
    """
    Represents the result of a specific checker's execution.
    """

    checker_name: str
    issues: list[Issue]
    execution_time_ms: float

    def __repr__(self) -> str:
        return f"CheckerResult(name={self.checker_name!r}, issues={len(self.issues)})"


class CheckReport(BaseModel):
    """
    Aggregate report of all ATS checks performed on a PDF document.
    """

    pdf_path: Path
    check_results: list[CheckerResult]
    score: float | None = Field(default=None, description="Overall ATS compatibility score")
    all_text: str | None = Field(default=None, description="Full text extracted from the PDF")
    timestamp: datetime = Field(default_factory=datetime.now)

    @computed_field
    def all_issues(self) -> list[Issue]:
        """Flattened list of all issues across all checkers."""
        return self._get_all_issues()

    def _get_all_issues(self) -> list[Issue]:
        """Internal helper to flatten issues."""
        return [issue for result in self.check_results for issue in result.issues]

    @computed_field
    def critical_count(self) -> int:
        """Count of critical issues."""
        return sum(1 for issue in self._get_all_issues() if issue.severity == Severity.CRITICAL)

    @computed_field
    def warning_count(self) -> int:
        """Count of warning issues."""
        return sum(1 for issue in self._get_all_issues() if issue.severity == Severity.WARNING)

    @computed_field
    def ok_count(self) -> int:
        """Count of OK status indicators."""
        return sum(1 for issue in self._get_all_issues() if issue.severity == Severity.OK)

    def __repr__(self) -> str:
        return (
            f"CheckReport(path={self.pdf_path.name}, "
            f"critical={self.critical_count}, warning={self.warning_count}, "
            f"score={self.score})"
        )


class CheckerConfig(BaseModel):
    """
    Base configuration model for ATS checkers.
    Specific checkers should inherit from this class to define their parameters.
    """

    pass


class ImageInfo(BaseModel):
    """
    Metadata for an image found in a PDF document.
    """

    page: int
    xref: int
    width: int
    height: int
    is_large: bool

    @field_validator("width", "height")
    @classmethod
    def must_be_positive(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("Dimension must be positive")
        return v
