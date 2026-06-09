# Phase 1: Foundation & Project Setup

> Set up the project skeleton, packaging, data models, and configuration system.
> This phase creates the bones that all other phases build on.

## Step 1.1 — Initialize Project Structure

**Goal:** Create the `src/ats_checker/` package layout and `pyproject.toml`.

- [x] Create directory structure:
  ```
  src/ats_checker/
  ├── __init__.py
  ├── __main__.py
  ├── cli.py
  ├── config.py
  ├── models.py
  ├── scoring.py
  ├── engine.py
  ├── pdf_utils.py
  ├── checkers/
  │   └── __init__.py
  └── reporters/
      └── __init__.py
  ```
- [x] Create `tests/` directory structure mirroring `src/ats_checker/`
- [x] Create `tests/fixtures/` directory for test PDFs
- [x] Create empty `__init__.py` files in every package

**Acceptance:** `python -c "import ats_checker"` succeeds (even if empty).

---

## Step 1.2 — Configure `pyproject.toml`

**Goal:** Set up modern Python packaging with all dependencies and tool configs.

- [x] Set project metadata:
  - Name: `ats-resume-checker`
  - Version: `0.1.0`
  - Python requirement: `>=3.11`
  - Description, authors, license, README path
- [x] Declare core dependencies:
  - `pdfplumber>=0.10`
  - `PyMuPDF>=1.23`
  - `typer>=0.9` (with `all` extra for Rich)
  - `rich>=13`
  - `pydantic>=2`
  - `pydantic-settings>=2`
- [x] Declare dev dependencies as optional group:
  - `pytest>=7`
  - `pytest-cov>=4`
  - `pytest-mock>=3`
  - `mypy>=1.5`
  - `ruff>=0.1`
- [x] Configure build system (hatchling or setuptools)
- [x] Add CLI entry point: `ats-check = "ats_checker.cli:app"`
- [x] Configure Ruff in `[tool.ruff]`:
  - Line length: 100
  - Target Python 3.11+
  - Enable isort rules
- [x] Configure mypy in `[tool.mypy]`:
  - Strict mode
  - Warn on unused ignores
- [x] Configure pytest in `[tool.pytest.ini_options]`:
  - testpaths = `tests`
  - Source root mapping
- [x] Add `[project.scripts]` entry point for CLI

**Acceptance:** `pip install -e ".[dev]"` succeeds and `ats-check --help` runs (even if minimal).

---

## Step 1.3 — Define Data Models (`models.py`)

**Goal:** Create the core data structures that flow through the entire system.

- [x] Define `Severity` enum:
  ```python
  class Severity(str, Enum):
      CRITICAL = "critical"
      WARNING = "warning"
      OK = "ok"
  ```
- [x] Define `Issue` dataclass/pydantic model:
  - `severity: Severity`
  - `title: str`
  - `detail: str`
  - `checker_name: str` — which checker produced this issue
  - `remediation: str | None = None` — actionable fix suggestion
  - `location: str | None = None` — e.g., "Page 2" or "Metadata"
- [x] Define `CheckerResult` model:
  - `checker_name: str`
  - `issues: list[Issue]`
  - `execution_time_ms: float`
- [x] Define `CheckReport` model (aggregate of all checks):
  - `pdf_path: Path`
  - `check_results: list[CheckerResult]`
  - `all_issues: list[Issue]` — computed property that flattens
  - `critical_count: int` — computed
  - `warning_count: int` — computed
  - `ok_count: int` — computed
  - `score: float | None = None` — populated by scoring module
  - `timestamp: datetime`
- [x] Define `CheckerConfig` model (base for checker-specific configs)
- [x] Add `__str__` and `__repr__` methods for all models
- [x] Add model validators (e.g., title must not be empty)

**Acceptance:** All models instantiate, validate, and serialize correctly. Type hints are complete.

---

## Step 1.4 — Configuration System (`config.py`)

**Goal:** Create a type-safe, layered configuration system.

- [ ] Define `Config` using Pydantic Settings:
  - Thresholds:
    - `max_file_size_kb: int = 1024`
    - `warning_file_size_kb: int = 500`
    - `min_text_length: int = 50`
    - `min_alpha_ratio: float = 0.6`
    - `warning_alpha_ratio: float = 0.4`
    - `column_gap_threshold: float = 100`
    - `min_words_for_column_check: int = 20`
    - `large_image_px: int = 72`
  - Sections:
    - `expected_sections: dict[str, list[str]]` — section name → keyword list
    - Default: experience, education, skills (same as current script)
  - Fonts:
    - `safe_fonts: set[str]` — known ATS-safe font names
    - `symbol_fonts: set[str]` — known problematic font names
  - Contact patterns:
    - `email_pattern: str` — regex pattern
    - `phone_patterns: list[str]` — regex patterns for phone numbers
  - Output:
    - `default_report_format: str = "terminal"`
    - `color_output: bool = True`
    - `verbose: bool = False`
  - Metadata:
    - `software_keywords: set[str]` — words that indicate software, not a person
- [ ] Support config file loading (`.toml` or `.yaml`)
- [ ] Support environment variable overrides (e.g., `ATS_CHECKER_MAX_FILE_SIZE_KB`)
- [ ] Support programmatic override in CLI flags
- [ ] Add `from_current_script()` class method that mirrors current `ats_check.py` defaults
- [ ] Validate config on load (e.g., warning threshold < critical threshold)

**Acceptance:** Config can be loaded from defaults, from file, from env vars, and merged correctly.

---

## Step 1.5 — PDF Utility Module (`pdf_utils.py`)

**Goal:** Centralize PDF loading, text extraction, and shared helpers.

- [ ] Create `PDFDocument` wrapper class:
  - Constructor takes `Path`, loads both pdfplumber and PyMuPDF documents
  - Implements context manager (`__enter__`/`__exit__`) for resource cleanup
  - Caches text extraction results per page
  - Properties: `page_count`, `file_size_kb`, `metadata`
- [ ] Create `extract_text(pdf: PDFDocument) -> str`:
  - Extracts all text from all pages using pdfplumber
  - Returns concatenated text with page breaks
- [ ] Create `extract_words(pdf: PDFDocument) -> list[dict]`:
  - Extracts word-level data with position info
  - Returns list of `{"text": ..., "x0": ..., "x1": ..., "top": ..., "bottom": ...}`
- [ ] Create `extract_images_info(pdf: PDFDocument) -> list[ImageInfo]`:
  - Returns structured image data (dimensions, page, xref)
  - Includes helper to classify image as large/small
- [ ] Create `extract_font_info(pdf: PDFDocument) -> set[str]`:
  - Returns normalized set of font names found in the document
- [ ] Add proper error handling:
  - `PDFCorruptedError` for unreadable files
  - `PDFPasswordError` for password-protected files
  - `ExtractionError` for general failures
- [ ] Add type hints throughout
- [ ] No side effects (no writing `.extracted.txt` — that's a reporter concern)

**Acceptance:** `PDFDocument` can open a test PDF and provide text, images, fonts, metadata without leaking resources.

---

## Step 1.6 — Package Exports (`__init__.py`)

**Goal:** Define the public API surface.

- [ ] In `src/ats_checker/__init__.py`:
  - Export `Config`, `CheckReport`, `Issue`, `Severity`, `CheckerResult`
  - Export `run_check()` function (will be implemented in Phase 2)
  - Define `__version__`
- [ ] In `src/ats_checker/checkers/__init__.py`:
  - Export `BaseChecker`, `CheckerRegistry`
- [ ] In `src/ats_checker/reporters/__init__.py`:
  - Export `BaseReporter`, `get_reporter()`

**Acceptance:** `from ats_checker import CheckReport, Issue, Severity` works.

---

## Step 1.7 — Development Environment Setup

**Goal:** Ensure every developer can get started with one command.

- [ ] Create `.gitignore` (Python, IDE, build artifacts, `__pycache__`, `.egg-info`, `dist/`, `.mypy_cache/`, `.pytest_cache/`)
- [ ] Create `requirements.txt` as a convenience (generated from `pyproject.toml`)
- [ ] Create `.python-version` pinning to 3.11+
- [ ] Verify `pip install -e ".[dev]"` installs everything
- [ ] Verify `python -m ats_checker` runs without error
- [ ] Verify `pytest` discovers tests (even if none exist yet)
- [ ] Verify `ruff check src/` passes on existing files
- [ ] Verify `mypy src/` passes on existing files

**Acceptance:** Fresh clone → `pip install -e ".[dev]"` → all tools run cleanly.

---

## Dependencies

- None — this is the first phase.

## Next Phase

→ [Phase 2: Checker Engine](phase-2-checker-engine.md)