from __future__ import annotations

import tomllib
from pathlib import Path

from pydantic import BaseModel, Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


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
    verbose: bool = False
    compact: bool = False


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


class Config(BaseSettings):
    """
    Main application configuration.
    Loaded from defaults -> config file -> environment variables -> overrides.
    """

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

    @classmethod
    def from_current_script(cls) -> Config:
        """
        Returns a Config instance with defaults that match the original ats_check.py script.
        """
        return cls()

    def load_from_file(self, path: Path) -> Config:
        """
        Loads configuration from a TOML file and updates the current config.
        """
        if not path.exists():
            return self

        if path.suffix == ".toml":
            with path.open("rb") as f:
                data = tomllib.load(f)
                # We update using model_copy to maintain the original instance's state
                # but with new data. BaseSettings supports nested updates via dict.
                return self.model_copy(update=data)

        return self
