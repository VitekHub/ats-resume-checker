"""Tests for custom validation rules and non-trivial computed properties in data models.

Tests behavior, not implementation (R1). Covers boundary conditions (R2) and public
validation rules (R3). Uses pytest.raises for error paths (R4) and parametrize for
multi-input scenarios (R5).

Skips (per X1–X6):
- Pydantic defaults / required-field enforcement (X1)
- Trivial len()/sum() counts — only one quick assert (X2)
- Third-party library behavior (X3)
- __repr__/__str__ format (X4)
- Duplicate unit/integration logic (X5)
- What mypy already catches (X6)
"""

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from ats_checker.config import FileSizeConfig, TextExtractionConfig
from ats_checker.models import (
    BatchReport,
    CheckerResult,
    CheckReport,
    ImageInfo,
    Issue,
    Severity,
)

# =============================================================================
# Helpers
# =============================================================================


def _make_issue(
    severity: Severity = Severity.OK,
    title: str = "Test issue",
    detail: str = "Test detail",
    checker_name: str = "test_checker",
) -> Issue:
    """Create an Issue with sensible defaults for test assertions."""
    return Issue(
        severity=severity,
        title=title,
        detail=detail,
        checker_name=checker_name,
    )


def _make_result(
    issues: list[Issue],
    checker_name: str = "test_checker",
) -> CheckerResult:
    """Create a CheckerResult wrapping the given issues."""
    return CheckerResult(checker_name=checker_name, issues=issues, execution_time_ms=1.0)


# =============================================================================
# Issue Validation
# =============================================================================


class TestIssueValidation:
    """Tests for Issue.must_not_be_empty validator and Severity enum coercion."""

    @pytest.mark.parametrize(
        "field, value",
        [
            ("title", ""),
            ("title", "   "),
            ("detail", ""),
            ("detail", "   "),
        ],
    )
    def test_empty_or_whitespace_fields_raise(self, field: str, value: str) -> None:
        """Empty or whitespace-only title/detail must raise ValidationError (R2, R4)."""
        kwargs: dict = {
            "severity": Severity.OK,
            "title": "Valid title",
            "detail": "Valid detail",
            "checker_name": "test",
        }
        kwargs[field] = value
        with pytest.raises(ValidationError, match="must not be empty"):
            Issue(**kwargs)

    def test_valid_issue_passes(self) -> None:
        """A properly formed Issue should instantiate without error."""
        issue = _make_issue(severity=Severity.CRITICAL, title="Big problem")
        assert issue.severity == Severity.CRITICAL
        assert issue.title == "Big problem"

    def test_invalid_severity_string_raises(self) -> None:
        """Passing an invalid severity string must raise ValidationError."""
        with pytest.raises(ValidationError):
            Issue(
                severity="bad",  # type: ignore[arg-type]
                title="Title",
                detail="Detail",
                checker_name="test",
            )


# =============================================================================
# ImageInfo Validation
# =============================================================================


class TestImageInfoValidation:
    """Tests for ImageInfo.must_be_positive validator on width/height."""

    @pytest.mark.parametrize(
        "field, value",
        [
            ("width", 0),
            ("width", -1),
            ("height", 0),
            ("height", -1),
        ],
    )
    def test_non_positive_dimensions_raise(self, field: str, value: int) -> None:
        """Zero or negative dimensions must raise ValidationError (R2, R4)."""
        kwargs: dict = {"page": 1, "xref": 1, "width": 100, "height": 200, "is_large": False}
        kwargs[field] = value
        with pytest.raises(ValidationError, match="positive"):
            ImageInfo(**kwargs)

    def test_positive_dimensions_pass(self) -> None:
        """Valid positive dimensions should instantiate without error."""
        info = ImageInfo(page=1, xref=1, width=100, height=200, is_large=True)
        assert info.width == 100
        assert info.height == 200


# =============================================================================
# CheckReport Computed Properties
# =============================================================================


class TestCheckReportComputed:
    """Tests for CheckReport computed fields: all_issues, severity counts."""

    def test_all_issues_flattens_multiple_results(self) -> None:
        """all_issues must flatten issues from all CheckerResults in order."""
        issue_a1 = _make_issue(Severity.CRITICAL, title="A1")
        issue_a2 = _make_issue(Severity.WARNING, title="A2")
        issue_b1 = _make_issue(Severity.OK, title="B1")
        issue_b2 = _make_issue(Severity.CRITICAL, title="B2")

        result_a = _make_result([issue_a1, issue_a2], checker_name="checker_a")
        result_b = _make_result([issue_b1, issue_b2], checker_name="checker_b")

        report = CheckReport(
            pdf_path=Path("test.pdf"),
            check_results=[result_a, result_b],
        )

        assert len(report.all_issues) == 4
        assert report.all_issues[0].title == "A1"
        assert report.all_issues[1].title == "A2"
        assert report.all_issues[2].title == "B1"
        assert report.all_issues[3].title == "B2"

    def test_all_issues_empty_when_no_results(self) -> None:
        """all_issues must return an empty list when there are no check results."""
        report = CheckReport(pdf_path=Path("empty.pdf"), check_results=[])
        assert report.all_issues == []

    def test_severity_counts_with_mixed_issues(self) -> None:
        """critical_count, warning_count, ok_count must match mixed-severity data."""
        result_1 = _make_result(
            [
                _make_issue(Severity.CRITICAL, title="c1"),
                _make_issue(Severity.WARNING, title="w1"),
            ]
        )
        result_2 = _make_result(
            [
                _make_issue(Severity.CRITICAL, title="c2"),
                _make_issue(Severity.WARNING, title="w2"),
                _make_issue(Severity.WARNING, title="w3"),
                _make_issue(Severity.OK, title="ok1"),
            ]
        )

        report = CheckReport(
            pdf_path=Path("mixed.pdf"),
            check_results=[result_1, result_2],
        )

        assert report.critical_count == 2
        assert report.warning_count == 3
        assert report.ok_count == 1


# =============================================================================
# BatchReport Computed Properties
# =============================================================================


class TestBatchReportComputed:
    """Tests for BatchReport computed fields: total, critical/warnings/passed counts."""

    @staticmethod
    def _make_report(
        critical: int = 0,
        warning: int = 0,
        ok: int = 0,
        pdf_name: str = "file.pdf",
    ) -> CheckReport:
        """Create a CheckReport with the specified number of issues per severity."""
        issues: list[Issue] = []
        issues.extend(_make_issue(Severity.CRITICAL, title=f"crit_{i}") for i in range(critical))
        issues.extend(_make_issue(Severity.WARNING, title=f"warn_{i}") for i in range(warning))
        issues.extend(_make_issue(Severity.OK, title=f"ok_{i}") for i in range(ok))
        return CheckReport(
            pdf_path=Path(pdf_name),
            check_results=[_make_result(issues)],
        )

    def test_total_files(self) -> None:
        """total_files must equal the number of reports (X2: one quick assert)."""
        reports = [self._make_report(pdf_name=f"file_{i}.pdf") for i in range(3)]
        batch = BatchReport(reports=reports)
        assert batch.total_files == 3

    def test_files_with_critical(self) -> None:
        """files_with_critical must count only reports with ≥1 critical issue."""
        reports = [
            self._make_report(critical=2, pdf_name="critical1.pdf"),
            self._make_report(critical=1, pdf_name="critical2.pdf"),
            self._make_report(warning=3, pdf_name="warnings_only.pdf"),
        ]
        batch = BatchReport(reports=reports)
        assert batch.files_with_critical == 2

    def test_files_with_warnings_no_critical(self) -> None:
        """files_with_warnings must count reports with warnings but no critical issues."""
        reports = [
            self._make_report(warning=2, pdf_name="warnings_only.pdf"),
            self._make_report(critical=1, warning=3, pdf_name="critical_and_warnings.pdf"),
            self._make_report(ok=1, pdf_name="clean.pdf"),
        ]
        batch = BatchReport(reports=reports)
        assert batch.files_with_warnings == 1

    def test_files_passed(self) -> None:
        """files_passed must count reports with no critical and no warning issues."""
        reports = [
            self._make_report(ok=2, pdf_name="clean.pdf"),
            self._make_report(critical=1, pdf_name="bad.pdf"),
            self._make_report(warning=1, pdf_name="warn.pdf"),
        ]
        batch = BatchReport(reports=reports)
        assert batch.files_passed == 1

    @pytest.mark.parametrize(
        "has_critical_flag, critical_count_in_first",
        [
            (True, 1),
            (False, 0),
        ],
    )
    def test_has_critical(self, has_critical_flag: bool, critical_count_in_first: int) -> None:
        """has_critical must be True when any report has critical issues."""
        reports = [
            self._make_report(critical=critical_count_in_first, pdf_name="first.pdf"),
            self._make_report(warning=2, pdf_name="second.pdf"),
        ]
        batch = BatchReport(reports=reports)
        assert batch.has_critical is has_critical_flag


# =============================================================================
# FileSizeConfig Validation
# =============================================================================


class TestFileSizeConfigValidation:
    """Tests for FileSizeConfig model_validator: warning_kb must be < critical_kb."""

    def test_warning_geq_critical_raises(self) -> None:
        """warning_kb >= critical_kb must raise ValidationError (R4)."""
        with pytest.raises(ValidationError, match="warning_kb must be less than critical_kb"):
            FileSizeConfig(warning_kb=1024, critical_kb=500)

    def test_warning_lt_critical_passes(self) -> None:
        """Valid threshold ordering must instantiate without error."""
        config = FileSizeConfig(warning_kb=500, critical_kb=1024)
        assert config.warning_kb == 500
        assert config.critical_kb == 1024

    def test_equal_thresholds_raises(self) -> None:
        """Equal thresholds must raise ValidationError — boundary condition (R2)."""
        with pytest.raises(ValidationError, match="warning_kb must be less than critical_kb"):
            FileSizeConfig(warning_kb=500, critical_kb=500)


# =============================================================================
# TextExtractionConfig Validation
# =============================================================================


class TestTextExtractionConfigValidation:
    """Tests for TextExtractionConfig model_validator: critical ratio must be < warning ratio."""

    def test_critical_geq_warning_raises(self) -> None:
        """alpha_ratio_critical >= alpha_ratio_warning must raise ValidationError (R4)."""
        with pytest.raises(ValidationError, match="alpha_ratio_critical must be less than"):
            TextExtractionConfig(alpha_ratio_critical=0.6, alpha_ratio_warning=0.4)

    def test_critical_lt_warning_passes(self) -> None:
        """Valid ratio ordering must instantiate without error."""
        config = TextExtractionConfig(alpha_ratio_critical=0.4, alpha_ratio_warning=0.6)
        assert config.alpha_ratio_critical == 0.4
        assert config.alpha_ratio_warning == 0.6

    def test_equal_ratios_raise(self) -> None:
        """Equal ratios must raise ValidationError — boundary condition (R2)."""
        with pytest.raises(ValidationError, match="alpha_ratio_critical must be less than"):
            TextExtractionConfig(alpha_ratio_critical=0.5, alpha_ratio_warning=0.5)
