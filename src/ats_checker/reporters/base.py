from abc import ABC, abstractmethod

from ..models import CheckReport


class BaseReporter(ABC):
    """
    Abstract Base Class for all report generators.
    """

    @abstractmethod
    def report(self, report: CheckReport) -> None:
        """
        Generate a report based on the results of the ATS checks.

        Args:
            report: The aggregate report to be rendered.
        """
        pass


def get_reporter(format: str) -> BaseReporter:
    """
    Factory function to retrieve a reporter based on the requested format.

    Args:
        format: The desired output format (e.g., 'terminal', 'json', 'html').

    Returns:
        An instance of a BaseReporter implementation.

    Raises:
        NotImplementedError: If the requested format is not yet implemented.
    """
    # Implementations will be added in Phase 3
    raise NotImplementedError(f"Reporter format '{format}' is not yet implemented.")
