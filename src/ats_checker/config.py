from __future__ import annotations

import tomllib
from pathlib import Path

from pydantic import BaseModel, Field, model_validator
from pydantic_settings import BaseSettings, PydanticBaseSettingsSource, SettingsConfigDict


class ConfigError(Exception):
    """Raised when there is an error loading or validating the configuration."""

    pass


class FileSizeConfig(BaseModel):
    """Configuration for file size limits."""

    warning_kb: int = 500
    critical_kb: int = 1024

    @model_validator(mode="after")
    def validate_thresholds(self) -> FileSizeConfig:
        if self.warning_kb >= self.critical_kb:
            raise ValueError("warning_kb must be less than critical_kb")
        return self


class ImageConfig(BaseModel):
    """Configuration for image size detection."""

    large_width_px: int = 72
    large_height_px: int = 72


class LayoutConfig(BaseModel):
    """Configuration for document layout analysis."""

    min_words_for_column_check: int = 20
    column_gap_threshold: int = 100


class TextExtractionConfig(BaseModel):
    """Configuration for text extraction quality assessment."""

    min_length_critical: int = 50
    alpha_ratio_critical: float = 0.4
    alpha_ratio_warning: float = 0.6

    @model_validator(mode="after")
    def validate_ratios(self) -> TextExtractionConfig:
        if self.alpha_ratio_critical >= self.alpha_ratio_warning:
            raise ValueError("alpha_ratio_critical must be less than alpha_ratio_warning")
        return self


class SectionConfig(BaseModel):
    """Configuration for resume section detection."""

    expected_sections: dict[str, list[str]] = Field(
        default={
            "experience": [
                "experience",
                "work experience",
                "employment",
                "professional experience",
                "work history",
                "career history",
            ],
            "education": ["education", "academic", "qualifications", "degree"],
            "skills": [
                "skills",
                "technical skills",
                "core competencies",
                "competencies",
                "technologies",
                "proficiencies",
            ],
        }
    )
    contact_patterns: list[str] = Field(
        default=[
            r"\b[\w.-]+@[\w.-]+\.\w{2,}\b",  # Email
            r"\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b",  # US-phone
            r"\b\d{3}\s\d{3}\s\d{3}\s\d{3}\b",  # Czech-style
            r"\b\+?\d[\d\s\-().]{7,}\d\b",  # International
        ]
    )


class FontConfig(BaseModel):
    """Configuration for font analysis."""

    safe_fonts: set[str] = Field(
        default={
            "arial",
            "helvetica",
            "timesnewroman",
            "times",
            "calibri",
            "garamond",
            "georgia",
            "verdana",
            "tahoma",
            "trebuchet",
            "courier",
            "couriernew",
            "dejavusans",
            "dejavuserif",
            "notosans",
            "roboto",
            "liberationsans",
            "liberationserif",
        }
    )
    symbol_fonts: set[str] = Field(
        default={"symbol", "wingdings", "zapfdingbats", "wingding", "mathfont", "symbolfont"}
    )
    embedded_prefixes: set[str] = Field(
        default={"cambria", "consola", "cfx", "aabcio", "nimbus", "noto", "source", "freesans"}
    )


class MetadataConfig(BaseModel):
    """Configuration for metadata analysis."""

    software_keywords: set[str] = Field(
        default={
            "microsoft",
            "adobe",
            "word",
            "latex",
            "libre",
            "ghost",
            "pdf",
            "writer",
            "chrome",
            "safari",
            "macos",
        }
    )


class OutputConfig(BaseModel):
    """Configuration for output reporting."""

    format: str = "terminal"
    color_output: bool = True
    verbose: bool = True
    compact: bool = False
    report_filename_suffix: str = "-ats-report"


class UnicodeConfig(BaseModel):
    """Configuration for special character detection."""

    problematic_ranges: list[tuple[int, int, str]] = Field(
        default=[
            (0x2000, 0x206F, "General Punctuation (em/en dashes, thin spaces, etc.)"),
            (0x2190, 0x21FF, "Arrows"),
            (0x2500, 0x257F, "Box drawing characters"),
            (0x25A0, 0x25FF, "Geometric shapes (bullets, squares)"),
            (0x2600, 0x26FF, "Miscellaneous symbols"),
            (0x2700, 0x27BF, "Dingbats"),
        ]
    )


class TomlConfigSettingsSource(PydanticBaseSettingsSource):
    """Custom source to load configuration from TOML files with a specific search order."""

    def __call__(self) -> dict[str, any]:
        """Resolve and merge TOML configuration files."""
        merged_data = {}

        # Search order (lowest to highest priority)
        config_paths = [
            # 1. XDG config
            Path.home() / ".config" / "ats-checker" / "config.toml",
            # 2. Local config
            Path.cwd() / "ats-checker.toml",
            # 3. Explicit config
            getattr(self.settings_cls, "_explicit_config_path", None),
        ]

        for path in config_paths:
            if path and isinstance(path, Path) and path.exists():
                try:
                    with path.open("rb") as f:
                        data = tomllib.load(f)
                        if isinstance(data, dict):
                            self._deep_update(merged_data, data)
                except tomllib.TOMLDecodeError as e:
                    raise ConfigError(f"Invalid TOML syntax in {path}: {e}") from e
                except OSError as e:
                    raise ConfigError(f"Could not read config file {path}: {e}") from e

        return merged_data

    def get_field_value(self, field, field_name):
        """Return None to let the main settings loop handle field resolution via the dict."""
        return None

    def _deep_update(self, source: dict, update: dict) -> None:
        """Recursively update a dictionary."""
        for key, value in update.items():
            if isinstance(value, dict) and key in source and isinstance(source[key], dict):
                self._deep_update(source[key], value)
            else:
                source[key] = value


class Config(BaseSettings):
    """
    Main application configuration.
    Loaded from defaults -> config file -> environment variables -> overrides.
    """

    _explicit_config_path: Path | None = None

    model_config = SettingsConfigDict(
        env_prefix="ATS_CHECKER_",
        env_nested_delimiter="__",
        case_sensitive=False,
    )

    file_size: FileSizeConfig = Field(default_factory=FileSizeConfig)
    images: ImageConfig = Field(default_factory=ImageConfig)
    layout: LayoutConfig = Field(default_factory=LayoutConfig)
    text: TextExtractionConfig = Field(default_factory=TextExtractionConfig)
    sections: SectionConfig = Field(default_factory=SectionConfig)
    fonts: FontConfig = Field(default_factory=FontConfig)
    metadata: MetadataConfig = Field(default_factory=MetadataConfig)
    output: OutputConfig = Field(default_factory=OutputConfig)
    unicode: UnicodeConfig = Field(default_factory=UnicodeConfig)

    def settings_customise_sources(
        cls,
        init_settings,
        env_settings,
        dotenv_settings,
        file_secret_settings,
    ):
        """
        Customise the priority of settings sources.
        Order (highest to lowest): Init Args -> Env Vars -> TOML Files -> Dotenv -> Secrets
        """
        return (
            init_settings,
            env_settings,
            TomlConfigSettingsSource(cls),
            dotenv_settings,
            file_secret_settings,
        )

    def show_effective_config(self) -> str:
        """Returns a string representation of the effective configuration."""
        import json

        return json.dumps(self.model_dump(mode="json"), indent=2)

    @classmethod
    def from_current_script(cls) -> Config:
        """
        Returns a Config instance with defaults that match the original ats_check.py script.
        """
        return cls()
