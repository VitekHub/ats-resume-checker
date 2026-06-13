"""Verify that the project foundation and test infrastructure are correctly set up."""

from ats_checker.config import Config
from ats_checker.models import Issue, Severity
from ats_checker.pdf_utils import PDFDocument


def test_core_imports():
    """Verify that all core modules can be imported."""
    from ats_checker import (
        checkers,  # noqa: F401
        engine,  # noqa: F401
        reporters,  # noqa: F401
    )

    assert True


def test_models_instantiation():
    """Verify that core model classes can be instantiated."""
    issue = Issue(
        severity=Severity.OK,
        title="Test issue",
        detail="Test detail",
        checker_name="test_checker",
    )
    assert issue.severity == Severity.OK
    assert issue.title == "Test issue"


def test_config_instantiation():
    """Verify that Config can be instantiated with defaults."""
    config = Config()
    assert config.file_size.warning_kb == 500
    assert config.file_size.critical_kb == 1024


def test_pdf_document_import():
    """Verify that PDFDocument is importable and context manager protocol exists."""
    assert hasattr(PDFDocument, "__enter__")
    assert hasattr(PDFDocument, "__exit__")


def test_severity_enum():
    """Verify that Severity enum has expected values."""
    assert Severity.CRITICAL.value == "critical"
    assert Severity.WARNING.value == "warning"
    assert Severity.OK.value == "ok"
