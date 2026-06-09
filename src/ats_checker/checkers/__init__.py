import importlib
import pkgutil
from pathlib import Path

from .base import BaseChecker
from .registry import CheckerRegistry

# Auto-discover and import all checker modules
# This ensures that @register_checker decorators are executed.
_package_path = Path(__file__).parent

for loader, module_name, is_pkg in pkgutil.iter_modules([str(_package_path)]):
    if module_name not in ("base", "registry"):
        importlib.import_module(f".{module_name}", package=__name__)

__all__ = ["BaseChecker", "CheckerRegistry"]
