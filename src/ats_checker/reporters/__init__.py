"""
Reporter registry and factory for ats_checker.
"""

# Import reporters to trigger their self-registration
from . import (
    html_reporter,  # noqa: F401
    json_reporter,  # noqa: F401
    terminal_reporter,  # noqa: F401
)
from .base import _REPORTERS, BaseReporter, register_reporter


def get_reporter(format_name: str) -> BaseReporter:
    """
    Return an instance of the reporter identified by `format_name`.

    Args:
        format_name: The name of the reporter format (e.g., "terminal", "json").

    Returns:
        An instance of the requested BaseReporter.

    Raises:
        ValueError: If no reporter is registered for the given format_name.
    """
    cls = _REPORTERS.get(format_name)
    if cls is None:
        raise ValueError(
            f"No reporter registered for format: {format_name!r}. "
            f"Available formats: {list_formats()}"
        )
    return cls()


def list_formats() -> list[str]:
    """
    Return a list of all registered reporter format names.
    """
    return list(_REPORTERS.keys())


__all__ = ["BaseReporter", "register_reporter", "get_reporter", "list_formats"]
