from typing import Dict, List, Type

from .base import BaseChecker


class CheckerRegistry:
    """
    Registry for ATS checkers. Handles registration and retrieval of
    checker classes.
    """

    _checkers: Dict[str, Type[BaseChecker]] = {}

    @classmethod
    def register(cls, checker_class: Type[BaseChecker]) -> Type[BaseChecker]:
        """
        Register a checker class.

        Args:
            checker_class: The checker class to register.

        Returns:
            The registered checker class.

        Raises:
            AttributeError: If the checker class does not have a 'name' attribute.
        """
        if not hasattr(checker_class, "name"):
            raise AttributeError(
                f"Checker class {checker_class.__name__} must have a 'name' attribute."
            )

        name = checker_class.name
        cls._checkers[name] = checker_class
        return checker_class

    @classmethod
    def get(cls, name: str) -> Type[BaseChecker]:
        """
        Retrieve a registered checker class by its name.

        Args:
            name: The name of the checker to retrieve.

        Returns:
            The checker class.

        Raises:
            KeyError: If no checker with the given name is registered.
        """
        if name not in cls._checkers:
            raise KeyError(f"Checker '{name}' is not registered.")
        return cls._checkers[name]

    @classmethod
    def get_all(cls) -> List[Type[BaseChecker]]:
        """
        Return all currently registered checker classes.

        Returns:
            A list of registered checker classes.
        """
        return list(cls._checkers.values())

    @classmethod
    def get_default(cls) -> List[Type[BaseChecker]]:
        """
        Return the standard set of checkers.

        Returns:
            A list of default checker classes.
        """
        return cls.get_all()


# Decorator for easy checker registration
register_checker = CheckerRegistry.register
