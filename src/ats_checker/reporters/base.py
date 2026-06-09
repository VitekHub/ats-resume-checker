from abc import ABC, abstractmethod
from pathlib import Path

from ..models import CheckReport


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
