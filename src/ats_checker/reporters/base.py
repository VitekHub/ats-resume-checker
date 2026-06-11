from abc import ABC, abstractmethod
from pathlib import Path
from typing import Type

from ..models import BatchReport, CheckReport

# Private registry mapping format_name -> reporter class
_REPORTERS: dict[str, Type["BaseReporter"]] = {}


def register_reporter(cls: Type["BaseReporter"]) -> Type["BaseReporter"]:
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


class BaseReporter(ABC):
    """
    Abstract Base Class for all report generators.
    """

    format_name: str  # e.g. "terminal", "json", "html"

    @abstractmethod
    def report(self, result: CheckReport, output: Path | None = None) -> str:
        """
        Generate a report from check results.

        Args:
            result: The check result to report on.
            output: Optional file path to write to. If None, return as string.

        Returns:
            The formatted report as a string.
        """
        ...

    def report_to_console(self, result: CheckReport) -> None:
        """
        Generate the report and print it to stdout.
        """
        print(self.report(result))

    @abstractmethod
    def report_batch(self, batch: BatchReport, output: Path | None = None) -> str:
        """
        Generate a batch report from multiple check results.

        Args:
            batch: The BatchReport containing multiple CheckReports.
            output: Optional file path to write to. If None, return as string.

        Returns:
            The formatted batch report as a string.
        """
        ...

    def report_batch_to_console(self, batch: BatchReport) -> None:
        """Print the batch report to stdout."""
        print(self.report_batch(batch))
