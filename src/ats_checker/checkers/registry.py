from typing import List, Type

from .base import BaseChecker


class CheckerRegistry:
    """
    Registry for managing and discovering ATS checkers.
    """

    _checkers: List[Type[BaseChecker]] = []

    @classmethod
    def register(cls, checker_cls: Type[BaseChecker]) -> None:
        """Registers a checker class for execution."""
        if checker_cls not in cls._checkers:
            cls._checkers.append(checker_cls)

    @classmethod
    def get_all_checkers(cls) -> List[BaseChecker]:
        """Instantiates and returns all registered checkers."""
        return [checker_cls() for checker_cls in cls._checkers]
