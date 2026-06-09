from pathlib import Path

from ..config import Config
from ..models import CheckReport
from .base import BaseReporter, register_reporter


@register_reporter
class JSONReporter(BaseReporter):
    """
    Reporter that produces a machine-readable JSON output of the ATS check results.
    """

    format_name = "json"

    def __init__(self) -> None:
        self._cfg = Config()

    def report(self, result: CheckReport, output: Path | None = None) -> str:
        """
        Generate a JSON report from check results.

        Args:
            result: The check report to serialize.
            output: Optional path to write the JSON output to.

        Returns:
            The serialized JSON report as a string.
        """
        # Determine indentation based on compact config
        indent = 2 if not self._cfg.output.compact else None

        # Serialize the Pydantic model to JSON
        json_report = result.model_dump_json(indent=indent)

        # Write to file if output path is provided
        if output:
            output.write_text(json_report, encoding="utf-8")

        return json_report
