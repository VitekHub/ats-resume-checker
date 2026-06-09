from abc import ABC, abstractmethod

from ..config import Config
from ..models import Issue, Severity
from ..pdf_utils import PDFDocument


class BaseChecker(ABC):
    """
    Abstract Base Class for all ATS checkers.
    Every new checker must inherit from this class and implement the `check` method.
    """

    # Class-level flag to indicate if the checker needs extracted text.
    # If True, the engine will ensure text is extracted before calling check().
    requires_text: bool = True

    # These attributes must be defined by subclasses
    name: str
    description: str
    severity_on_fail: Severity

    def __init__(self, config: Config) -> None:
        """
        Initialize the checker with the application configuration.

        Args:
            config: The Pydantic settings configuration object.
        """
        self.config = config

    @abstractmethod
    def check(self, pdf: PDFDocument) -> list[Issue]:
        """
        Run this checker against the PDF and return any issues found.

        Args:
            pdf: The wrapped PDF document containing extracted data and cached results.

        Returns:
            A list of Issue objects found by this checker.
        """
        pass

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} name={self.name}>"

    def __str__(self) -> str:
        return self.name
