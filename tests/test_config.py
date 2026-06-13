"""Tests for configuration loading, merging, validation, and end-to-end propagation.

Covers step 5.3 requirements:
- TOML config file loading (partial, full, invalid)
- Environment variable overrides
- Config merging priority (defaults < TOML < env vars < init args)
- Custom validation rules
- Config values reaching checkers (R8)

Skips (per X1/X6):
- Pydantic Settings defaults behavior
- What mypy already catches
"""

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from ats_checker.checkers.file_size import FileSizeChecker
from ats_checker.checkers.text_extraction import TextExtractionChecker
from ats_checker.config import (
    Config,
    ConfigError,
    FileSizeConfig,
    SectionConfig,
    TextExtractionConfig,
)
from ats_checker.pdf_utils import PDFDocument

from .helpers import create_test_pdf

# =============================================================================
# TOML Config Loading
# =============================================================================


class TestTomlConfigLoading:
    """Tests for loading configuration from TOML files."""

    def test_partial_toml_uses_defaults(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Partial TOML config: missing keys should fall back to defaults."""
        toml_file = tmp_path / "partial.toml"
        toml_file.write_text(
            """
[file_size]
warning_kb = 300
critical_kb = 800
"""
        )
        # Prevent picking up real system configs
        monkeypatch.setattr(Path, "home", lambda: tmp_path / "nohome")
        monkeypatch.setattr(Path, "cwd", lambda: tmp_path / "nocwd")

        config = Config(config_file=toml_file)

        # Overridden values from TOML
        assert config.file_size.warning_kb == 300
        assert config.file_size.critical_kb == 800

        # Values not in TOML should use defaults
        assert config.text.min_length_critical == 50
        assert config.text.alpha_ratio_critical == 0.4
        assert config.text.alpha_ratio_warning == 0.6
        assert config.layout.min_words_for_column_check == 20

    def test_full_toml_overrides_all(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Full TOML config: all values should be overridden."""
        toml_file = tmp_path / "full.toml"
        toml_file.write_text(
            """
[file_size]
warning_kb = 200
critical_kb = 500

[images]
large_width_px = 100
large_height_px = 100

[layout]
min_words_for_column_check = 50
column_gap_threshold = 200

[text]
min_length_critical = 200
alpha_ratio_critical = 0.3
alpha_ratio_warning = 0.5

[output]
format = "json"
color_output = false
verbose = false
compact = true
"""
        )
        monkeypatch.setattr(Path, "home", lambda: tmp_path / "nohome")
        monkeypatch.setattr(Path, "cwd", lambda: tmp_path / "nocwd")

        config = Config(config_file=toml_file)

        assert config.file_size.warning_kb == 200
        assert config.file_size.critical_kb == 500
        assert config.images.large_width_px == 100
        assert config.images.large_height_px == 100
        assert config.layout.min_words_for_column_check == 50
        assert config.layout.column_gap_threshold == 200
        assert config.text.min_length_critical == 200
        assert config.text.alpha_ratio_critical == 0.3
        assert config.text.alpha_ratio_warning == 0.5
        assert config.output.format == "json"
        assert config.output.color_output is False
        assert config.output.verbose is False
        assert config.output.compact is True

    def test_invalid_toml_syntax_raises(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Invalid TOML syntax should raise ConfigError."""
        toml_file = tmp_path / "bad.toml"
        toml_file.write_text("invalid toml [[[")

        monkeypatch.setattr(Path, "home", lambda: tmp_path / "nohome")
        monkeypatch.setattr(Path, "cwd", lambda: tmp_path / "nocwd")

        with pytest.raises(ConfigError, match="Invalid TOML"):
            Config(config_file=toml_file)

    def test_toml_nonexistent_file_uses_defaults(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A nonexistent config_file path should still load defaults."""
        nonexistent = tmp_path / "does_not_exist.toml"

        monkeypatch.setattr(Path, "home", lambda: tmp_path / "nohome")
        monkeypatch.setattr(Path, "cwd", lambda: tmp_path / "nocwd")

        # Should not raise — file is simply skipped
        config = Config(config_file=nonexistent)
        assert config.file_size.warning_kb == 500
        assert config.file_size.critical_kb == 1024

    def test_toml_nested_dict_section(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """TOML with nested dict sections (e.g. expected_sections) should parse."""
        toml_file = tmp_path / "nested.toml"
        toml_file.write_text(
            """
[sections.expected_sections]
experience = ["experience", "work experience"]
education = ["education"]

[sections]
contact_patterns = ["test@pattern"]
"""
        )
        monkeypatch.setattr(Path, "home", lambda: tmp_path / "nohome")
        monkeypatch.setattr(Path, "cwd", lambda: tmp_path / "nocwd")

        config = Config(config_file=toml_file)

        assert "experience" in config.sections.expected_sections
        assert config.sections.expected_sections["experience"] == [
            "experience",
            "work experience",
        ]
        assert config.sections.contact_patterns == ["test@pattern"]


# =============================================================================
# Environment Variables
# =============================================================================


class TestEnvironmentVariables:
    """Tests for config overrides via environment variables."""

    def test_env_var_override_nested(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """ATS_CHECKER__NESTED__KEY env var should override nested config values."""
        monkeypatch.setenv("ATS_CHECKER_FILE_SIZE__WARNING_KB", "300")
        monkeypatch.setenv("ATS_CHECKER_FILE_SIZE__CRITICAL_KB", "800")

        try:
            config = Config()
            assert config.file_size.warning_kb == 300
            assert config.file_size.critical_kb == 800
        finally:
            monkeypatch.delenv("ATS_CHECKER_FILE_SIZE__WARNING_KB", raising=False)
            monkeypatch.delenv("ATS_CHECKER_FILE_SIZE__CRITICAL_KB", raising=False)

    def test_env_var_override_output(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """ATS_CHECKER_OUTPUT__FORMAT env var should override output config."""
        monkeypatch.setenv("ATS_CHECKER_OUTPUT__FORMAT", "json")
        monkeypatch.setenv("ATS_CHECKER_OUTPUT__COLOR_OUTPUT", "false")

        try:
            config = Config()
            assert config.output.format == "json"
            assert config.output.color_output is False
        finally:
            monkeypatch.delenv("ATS_CHECKER_OUTPUT__FORMAT", raising=False)
            monkeypatch.delenv("ATS_CHECKER_OUTPUT__COLOR_OUTPUT", raising=False)

    def test_env_var_overrides_toml(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Env vars should take priority over TOML file values."""
        toml_file = tmp_path / "config.toml"
        toml_file.write_text(
            """
[file_size]
warning_kb = 300
critical_kb = 800
"""
        )
        monkeypatch.setattr(Path, "home", lambda: tmp_path / "nohome")
        monkeypatch.setattr(Path, "cwd", lambda: tmp_path / "nocwd")
        monkeypatch.setenv("ATS_CHECKER_FILE_SIZE__WARNING_KB", "100")

        try:
            config = Config(config_file=toml_file)
            # Env var (100) overrides TOML value (300)
            assert config.file_size.warning_kb == 100
            # TOML value still applies for fields not overridden by env
            assert config.file_size.critical_kb == 800
        finally:
            monkeypatch.delenv("ATS_CHECKER_FILE_SIZE__WARNING_KB", raising=False)


# =============================================================================
# Config Merging Priority
# =============================================================================


class TestConfigMergingPriority:
    """Tests that config sources are layered correctly:
    init args > env vars > TOML files > dotenv > secrets > defaults.
    """

    def test_defaults_used_when_no_overrides(self) -> None:
        """Plain Config() with no overrides should use all defaults."""
        config = Config()
        assert config.file_size.warning_kb == 500
        assert config.file_size.critical_kb == 1024
        assert config.text.min_length_critical == 50
        assert config.text.alpha_ratio_critical == 0.4
        assert config.text.alpha_ratio_warning == 0.6
        assert config.layout.min_words_for_column_check == 20
        assert config.layout.column_gap_threshold == 100
        assert config.output.format == "terminal"
        assert config.output.color_output is True
        assert config.output.verbose is True

    def test_toml_overrides_defaults(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """TOML file values should override defaults."""
        toml_file = tmp_path / "override.toml"
        toml_file.write_text(
            """
[file_size]
warning_kb = 300
critical_kb = 800
"""
        )
        monkeypatch.setattr(Path, "home", lambda: tmp_path / "nohome")
        monkeypatch.setattr(Path, "cwd", lambda: tmp_path / "nocwd")

        config = Config(config_file=toml_file)
        assert config.file_size.warning_kb == 300
        assert config.file_size.critical_kb == 800

    def test_env_overrides_toml(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Environment variables should override TOML values."""
        toml_file = tmp_path / "base.toml"
        toml_file.write_text(
            """
[file_size]
warning_kb = 300
critical_kb = 800
"""
        )
        monkeypatch.setattr(Path, "home", lambda: tmp_path / "nohome")
        monkeypatch.setattr(Path, "cwd", lambda: tmp_path / "nocwd")
        monkeypatch.setenv("ATS_CHECKER_FILE_SIZE__WARNING_KB", "100")

        try:
            config = Config(config_file=toml_file)
            # Env overrides TOML
            assert config.file_size.warning_kb == 100
            # TOML still applies where not overridden
            assert config.file_size.critical_kb == 800
        finally:
            monkeypatch.delenv("ATS_CHECKER_FILE_SIZE__WARNING_KB", raising=False)

    def test_init_overrides_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Explicit init args should override environment variables."""
        monkeypatch.setenv("ATS_CHECKER_FILE_SIZE__WARNING_KB", "300")

        try:
            config = Config(file_size=FileSizeConfig(warning_kb=100, critical_kb=500))
            # Init arg (100) overrides env var (300)
            assert config.file_size.warning_kb == 100
        finally:
            monkeypatch.delenv("ATS_CHECKER_FILE_SIZE__WARNING_KB", raising=False)


# =============================================================================
# Config Validation (custom rules only)
# =============================================================================


class TestConfigValidation:
    """Tests for custom validation rules propagated through Config.

    Sub-model validators (FileSizeConfig, TextExtractionConfig) are also
    tested in test_models.py; here we verify they propagate through the
    Config wrapper and test new validators.
    """

    def test_file_size_warning_geq_critical_raises(self) -> None:
        """warning_kb >= critical_kb must raise ValidationError through Config."""
        with pytest.raises(ValidationError, match="warning_kb must be less than critical_kb"):
            Config(file_size=FileSizeConfig(warning_kb=1024, critical_kb=500))

    def test_file_size_equal_thresholds_raises(self) -> None:
        """Equal thresholds must raise ValidationError — boundary (R2)."""
        with pytest.raises(ValidationError, match="warning_kb must be less than critical_kb"):
            Config(file_size=FileSizeConfig(warning_kb=500, critical_kb=500))

    def test_text_extraction_negative_min_length_raises(self) -> None:
        """min_length_critical < 0 must raise ValidationError."""
        with pytest.raises(ValidationError, match="min_length_critical must be non-negative"):
            Config(text=TextExtractionConfig(min_length_critical=-1))

    def test_text_extraction_zero_min_length_passes(self) -> None:
        """min_length_critical == 0 is valid (disables length check) — boundary (R2)."""
        config = Config(text=TextExtractionConfig(min_length_critical=0))
        assert config.text.min_length_critical == 0

    def test_text_extraction_ratio_order_raises(self) -> None:
        """alpha_ratio_critical >= alpha_ratio_warning must raise ValidationError."""
        with pytest.raises(ValidationError, match="alpha_ratio_critical must be less than"):
            Config(text=TextExtractionConfig(alpha_ratio_critical=0.6, alpha_ratio_warning=0.4))

    def test_empty_expected_sections_raises(self) -> None:
        """Empty expected_sections dict must raise ValidationError."""
        with pytest.raises(ValidationError, match="expected_sections must not be empty"):
            Config(sections=SectionConfig(expected_sections={}))


# =============================================================================
# Config Reaches Checkers (R8)
# =============================================================================


class TestConfigReachesCheckers:
    """End-to-end tests verifying config values propagate to checker behavior (R8).

    Uses real PDFs and real checkers — tests that a checker with custom
    thresholds behaves differently from one with defaults.
    """

    def test_file_size_checker_custom_warning_threshold(self, tmp_path: Path) -> None:
        """FileSizeChecker with custom thresholds flags PDF as WARNING."""
        # create_test_pdf produces a ~400KB PDF with PyMuPDF overhead
        pdf_bytes = create_test_pdf(text="Small file content\n" * 10, pages=1)
        pdf_path = tmp_path / "small.pdf"
        pdf_path.write_bytes(pdf_bytes)

        # Default config: warning=500KB, critical=1024KB — file (~400KB) is OK
        default_config = Config()
        with PDFDocument(pdf_path) as pdf:
            issues = FileSizeChecker(default_config).check(pdf)
        assert all(i.severity.value == "ok" for i in issues)

        # Custom config: warning=200KB, critical=500KB — same file (~400KB) is WARNING
        custom_config = Config(file_size=FileSizeConfig(warning_kb=200, critical_kb=500))
        with PDFDocument(pdf_path) as pdf:
            issues = FileSizeChecker(custom_config).check(pdf)
        # File ~400KB is between 200KB warning and 500KB critical → WARNING
        assert any(i.severity.value == "warning" for i in issues)

    def test_file_size_checker_custom_critical_threshold(self, tmp_path: Path) -> None:
        """FileSizeChecker with very low critical threshold flags PDFs as CRITICAL."""
        # create_test_pdf produces a ~400KB PDF with PyMuPDF overhead
        pdf_bytes = create_test_pdf(text="Tiny content", pages=1)
        pdf_path = tmp_path / "tiny.pdf"
        pdf_path.write_bytes(pdf_bytes)

        # Config with very low critical threshold — file (~400KB) far exceeds 1KB
        custom_config = Config(file_size=FileSizeConfig(warning_kb=0, critical_kb=1))
        with PDFDocument(pdf_path) as pdf:
            issues = FileSizeChecker(custom_config).check(pdf)
        # File ~400KB > 1KB → CRITICAL
        assert any(i.severity.value == "critical" for i in issues)

    def test_text_extraction_checker_custom_thresholds(self, tmp_path: Path) -> None:
        """TextExtractionChecker with high min_length threshold flags short text."""
        # Create a PDF with short text (~30 chars)
        pdf_bytes = create_test_pdf(text="Short text", pages=1)
        pdf_path = tmp_path / "short.pdf"
        pdf_path.write_bytes(pdf_bytes)

        # Default config: min_length_critical=50, short text would be CRITICAL
        # But let's test with a custom high threshold to show config reaches checker
        custom_config = Config(
            text=TextExtractionConfig(
                min_length_critical=500,
                alpha_ratio_critical=0.3,
                alpha_ratio_warning=0.5,
            )
        )
        with PDFDocument(pdf_path) as pdf:
            issues = TextExtractionChecker(custom_config).check(pdf)
        # Text is far shorter than 500 chars → CRITICAL
        assert any(i.severity.value == "critical" for i in issues)

    def test_text_extraction_checker_lenient_thresholds(self, tmp_path: Path) -> None:
        """TextExtractionChecker with lenient thresholds accepts short text."""
        # Create a PDF with short text (~30 chars)
        pdf_bytes = create_test_pdf(text="Short text for testing", pages=1)
        pdf_path = tmp_path / "short2.pdf"
        pdf_path.write_bytes(pdf_bytes)

        # Config with very low threshold: anything with 1+ char passes length check
        custom_config = Config(
            text=TextExtractionConfig(
                min_length_critical=1,
                alpha_ratio_critical=0.1,
                alpha_ratio_warning=0.2,
            )
        )
        with PDFDocument(pdf_path) as pdf:
            issues = TextExtractionChecker(custom_config).check(pdf)
        # With min_length_critical=1, short text passes the length check
        # (may still trigger alpha ratio check, but not the length check)
        has_length_critical = any("Almost no extractable text" in i.detail for i in issues)
        assert not has_length_critical

    def test_env_var_override_reaches_checker(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Config from env var should propagate to checker behavior (R8)."""
        # Set both warning and critical thresholds to very low values via env vars
        # Must satisfy warning_kb < critical_kb validator
        monkeypatch.setenv("ATS_CHECKER_FILE_SIZE__WARNING_KB", "0")
        monkeypatch.setenv("ATS_CHECKER_FILE_SIZE__CRITICAL_KB", "1")

        try:
            config = Config()
            # Create a small PDF (~2-5KB)
            pdf_bytes = create_test_pdf(text="Env var test", pages=1)
            pdf_path = tmp_path / "env_test.pdf"
            pdf_path.write_bytes(pdf_bytes)

            with PDFDocument(pdf_path) as pdf:
                issues = FileSizeChecker(config).check(pdf)
            # File > 1KB → should be CRITICAL with env-var-overridden threshold
            assert any(i.severity.value == "critical" for i in issues)
        finally:
            monkeypatch.delenv("ATS_CHECKER_FILE_SIZE__WARNING_KB", raising=False)
            monkeypatch.delenv("ATS_CHECKER_FILE_SIZE__CRITICAL_KB", raising=False)
