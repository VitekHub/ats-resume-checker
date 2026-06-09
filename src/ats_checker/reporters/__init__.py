"""
Reporter registry and factory for ats_checker.
"""

from typing import Type

from .base import BaseReporter

# Private registry mapping format_name -> reporter class
_REPORTERS: dict[str, Type[BaseReporter]] = {}


def register_reporter(cls: Type[BaseReporter]) -> Type[BaseReporter]:
    """
    Class decorator for reporter subclasses.

    Registers the class in `_REPORTERS` using its `format_name`.
    """
    if not hasattr(cls, "format_name"):
        raise AttributeError(f"{cls.__name__} must define a class attribute `format_name`.")

    name = cls.format_name
    if name in _REPORTERS:
        raise ValueError(f"Reporter already registered for format: {name!r}")

    _REPORTERS[name] = cls
    return cls


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
