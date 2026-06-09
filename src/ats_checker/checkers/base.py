from abc import ABC, abstractmethod

from ..config import Config
from ..models import CheckerResult
from ..pdf_utils import PDFDocument


class BaseChecker(ABC):
    """
    Abstract Base Class for all ATS checkers.
    Every new checker must inherit from this class and implement the `check` method.
    """

    @property
    def name(self) -> str:
        """The unique name of the checker."""
        return self.__class__.__name__

    @abstractmethod
    def check(self, pdf: PDFDocument, config: Config) -> CheckerResult:
        """
        Perform the ATS compatibility check on the given PDF document.

        Args:
            pdf: The wrapped PDF document with cached extraction results.
            config: The application configuration.

        Returns:
            A CheckerResult containing any issues found during the check.
        """
        pass
