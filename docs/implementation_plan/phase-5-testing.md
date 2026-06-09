# Phase 5: Testing

> Build a comprehensive test suite: unit tests for every checker, integration
> tests for the full pipeline, fixtures for edge cases, and coverage targets.

## Step 5.1 — Test Infrastructure Setup

**Goal:** Set up pytest, fixtures, and test helpers.

- [ ] Create `tests/conftest.py` with shared fixtures:
  - `sample_config()` — returns a `Config` with test defaults
  - `clean_pdf()` — returns a `PDFDocument` for a well-formed resume
  - `scanned_pdf()` — returns a `PDFDocument` for a scanned image PDF
  - `multicolumn_pdf()` — returns a `PDFDocument` for a two-column resume
  - `empty_pdf()` — returns a `PDFDocument` for a PDF with no text
  - `tmp_pdf_path()` — returns a temporary PDF file path
- [ ] Create `tests/fixtures/` directory with test PDF files:
  - `clean_resume.pdf` — a simple, ATS-friendly resume
  - `scanned_image.pdf` — a PDF that's a scanned image (no extractable text)
  - `multicolumn.pdf` — a two-column layout resume
  - `unusual_fonts.pdf` — uses Wingdings or other symbol fonts
  - `metadata_leak.pdf` — has personal info in PDF metadata
  - `large_file.pdf` — exceeds 1 MB
  - `special_chars.pdf` — contains em dashes, bullets, box-drawing chars
  - `no_contact.pdf` — missing email and phone
  - `table_layout.pdf` — contains tables
- [ ] Create `tests/helpers.py` with:
  - `create_test_pdf()` — generates a simple PDF with given text (using reportlab or fpdf2)
  - `create_scanned_pdf()` — generates a PDF that's an image with text baked in
  - `assert_issue()` — helper to assert an Issue has expected severity and title
- [ ] Add `pytest.ini_options` configuration in `pyproject.toml`:
  - `testpaths = ["tests"]`
  - `python_files = ["test_*.py"]`
  - `addopts = "--tb=short -q"`

**Acceptance:** `pytest` discovers and runs all tests. Fixtures load correctly.

---

## Step 5.2 — Model Tests (`tests/test_models.py`)

**Goal:** Test all data models for correctness and validation.

- [ ] Test `Severity` enum:
  - All three values exist (CRITICAL, WARNING, OK)
  - String comparison works (`Severity.CRITICAL == "critical"`)
- [ ] Test `Issue` model:
  - Creating with required fields works
  - `remediation` and `location` default to `None`
  - Empty title raises validation error
  - `checker_name` is required
  - `__str__` produces readable output
- [ ] Test `CheckerResult` model:
  - Computed properties work (`all_issues`, `critical_count`, etc.)
  - Empty issues list is valid
- [ ] Test `CheckReport` model:
  - Flattening `check_results` into `all_issues` works
  - `critical_count`, `warning_count`, `ok_count` computed correctly
  - `timestamp` defaults to current time
  - `score` defaults to `None`

**Acceptance:** All model tests pass. Validation rules are enforced.

---

## Step 5.3 — Configuration Tests (`tests/test_config.py`)

**Goal:** Test configuration loading, merging, and validation.

- [ ] Test default config:
  - All default values are sensible
  - `Config()` with no arguments works
- [ ] Test config from TOML file:
  - Load a partial TOML config → missing keys use defaults
  - Load a full TOML config → all values overridden
- [ ] Test config from environment variables:
  - `ATS_CHECKER_MAX_FILE_SIZE_KB=2048` → override works
- [ ] Test config merging:
  - Defaults ← file ← env vars ← CLI → each layer overrides correctly
- [ ] Test config validation:
  - `warning_file_size_kb > max_file_size_kb` → validation error
  - `min_text_length < 0` → validation error
  - Empty `expected_sections` → validation error

**Acceptance:** Config tests pass for all loading and validation scenarios.

---

## Step 5.4 — PDF Utilities Tests (`tests/test_pdf_utils.py`)

**Goal:** Test PDF loading, text extraction, and helper functions.

- [ ] Test `PDFDocument`:
  - Opens valid PDF without error
  - Context manager closes resources
  - `page_count` returns correct value
  - `file_size_kb` returns correct value
  - Raises `PDFCorruptedError` for corrupted files
- [ ] Test `extract_text()`:
  - Returns all text from a multi-page PDF
  - Returns empty string for image-only PDF
  - Caches results (second call doesn't re-extract)
- [ ] Test `extract_words()`:
  - Returns word list with position data
  - Returns empty list for image-only PDF
- [ ] Test `extract_images_info()`:
  - Returns image data for PDFs with images
  - Returns empty list for text-only PDFs
  - Classifies large vs small correctly
- [ ] Test `extract_font_info()`:
  - Returns set of normalized font names
  - Returns empty set for image-only PDFs

**Acceptance:** All PDF utility functions work correctly with test fixtures.

---

## Step 5.5 — Checker Unit Tests

**Goal:** Test each checker in isolation with controlled inputs.

### `tests/checkers/test_file_size.py`
- [ ] Small file (< 500 KB) → OK
- [ ] Medium file (500–1024 KB) → WARNING
- [ ] Large file (> 1024 KB) → CRITICAL
- [ ] Custom thresholds in config override defaults

### `tests/checkers/test_images.py`
- [ ] PDF with no images → OK
- [ ] PDF with large images → CRITICAL
- [ ] PDF with small images only → WARNING
- [ ] PDF with both → both issues reported

### `tests/checkers/test_text_extraction.py`
- [ ] Good text extraction → OK
- [ ] Very short text (< 50 chars) → CRITICAL
- [ ] Low alpha ratio (< 0.4) → CRITICAL (garbled)
- [ ] Medium alpha ratio (0.4–0.6) → WARNING
- [ ] High alpha ratio (> 0.6) → OK
- [ ] Custom thresholds respected

### `tests/checkers/test_layout.py`
- [ ] Single-column layout → OK
- [ ] Two-column layout → WARNING
- [ ] Table layout → WARNING
- [ ] PDF with few words (< `min_words_for_column_check`) → skip column check

### `tests/checkers/test_sections.py`
- [ ] All sections present → OK
- [ ] Missing "experience" → WARNING
- [ ] Missing "education" → WARNING
- [ ] Custom section definitions in config

### `tests/checkers/test_contact_info.py`
- [ ] Email + phone present → OK
- [ ] Missing email → CRITICAL
- [ ] Missing phone → WARNING
- [ ] Various phone formats (US, Czech, international)
- [ ] Custom regex patterns in config

### `tests/checkers/test_fonts.py`
- [ ] All safe fonts → OK
- [ ] Symbol font (Wingdings) → CRITICAL
- [ ] Unusual fonts → WARNING
- [ ] Mixed safe and unsafe → WARNING
- [ ] Custom safe/symbol font lists in config

### `tests/checkers/test_metadata.py`
- [ ] Clean metadata → OK
- [ ] Personal name in author field → WARNING
- [ ] Software name in creator field → OK (not flagged)
- [ ] Multiple sensitive fields → single WARNING

### `tests/checkers/test_special_chars.py`
- [ ] No special characters → OK
- [ ] Em dash (U+2014) → WARNING
- [ ] Bullet (U+2022) → WARNING
- [ ] Box drawing chars → WARNING
- [ ] Multiple categories → single WARNING with details

**Acceptance:** All checker unit tests pass. Each checker is tested in isolation.

---

## Step 5.6 — Engine Integration Tests (`tests/test_engine.py`)

**Goal:** Test the full check pipeline end-to-end.

- [ ] Test `run_check()` with a clean PDF:
  - Returns `CheckReport` with all checkers
  - No CRITICAL issues
  - Has correct counts
- [ ] Test `run_check()` with a problematic PDF:
  - Returns CRITICAL and WARNING issues
  - All checkers ran
- [ ] Test `run_check()` with `checkers` filter:
  - Only specified checkers run
  - `CheckReport.check_results` has only those checkers
- [ ] Test `run_check()` with `skip_checkers`:
  - Specified checkers are skipped
  - Others still run
- [ ] Test error handling:
  - A checker that raises an exception → caught, recorded as CRITICAL issue, others continue
- [ ] Test that `requires_text` optimization works:
  - If only `file_size` checker is selected, text extraction is skipped

**Acceptance:** Full pipeline tests pass. Error handling is robust.

---

## Step 5.7 — Reporter Tests

### `tests/reporters/test_terminal.py`
- [ ] Output contains all issue titles
- [ ] CRITICAL issues appear in red
- [ ] WARNING issues appear in yellow
- [ ] OK issues appear in green
- [ ] `--no-color` produces plain text output
- [ ] `--verbose` includes OK issues
- [ ] Non-verbose mode omits OK issues

### `tests/reporters/test_json_reporter.py`
- [ ] Output is valid JSON
- [ ] Round-trip: `CheckReport.model_validate_json(json_str)` recovers data
- [ ] All fields present (checker names, severities, details)
- [ ] File output works when `output` path is provided

### `tests/reporters/test_html_reporter.py`
- [ ] Output is valid HTML
- [ ] No XSS vulnerabilities (PDF content is escaped)
- [ ] Contains all issue titles and details
- [ ] File output works when `output` path is provided
- [ ] Print CSS present

**Acceptance:** All reporter tests pass. Output formats are correct and safe.

---

## Step 5.8 — CLI Integration Tests (`tests/test_cli.py`)

**Goal:** Test the CLI interface end-to-end using Typer's test runner.

- [ ] `ats-check check resume.pdf` → runs and exits 0 for clean PDF
- [ ] `ats-check check problematic.pdf` → runs and exits 1
- [ ] `ats-check check nonexistent.pdf` → exits 2 with error
- [ ] `ats-check check resume.pdf --format json -o out.json` → creates JSON file
- [ ] `ats-check check resume.pdf --format html -o out.html` → creates HTML file
- [ ] `ats-check check resume.pdf --checker file_size --checker images` → runs only those
- [ ] `ats-check check resume.pdf --skip-checker fonts` → skips fonts
- [ ] `ats-check list-checkers` → lists all checker names
- [ ] `ats-check check resume.pdf --verbose` → shows OK issues
- [ ] `ats-check check resume.pdf --no-color` → no ANSI codes
- [ ] `ats-check check resume.pdf --config custom.toml` → loads custom config

**Acceptance:** All CLI integration tests pass. Exit codes are correct.

---

## Step 5.9 — Coverage & Quality Gates

**Goal:** Set coverage targets and quality checks.

- [ ] Configure pytest-cov in `pyproject.toml`:
  - Minimum coverage: 80%
  - Fail under threshold
- [ ] Add coverage exclusion patterns:
  - `tests/`
  - `**/__main__.py`
  - `**/conftest.py`
- [ ] Create `Makefile` or script with test commands:
  - `make test` — run all tests
  - `make test-cov` — run with coverage report
  - `make test-integration` — run only integration tests
  - `make lint` — run ruff
  - `make typecheck` — run mypy
  - `make check` — run lint + typecheck + test

**Acceptance:** `pytest --cov=ats_checker --cov-fail-under=80` passes.

---

## Dependencies

- **Phases 1–4** must be complete (full implementation needed for integration tests)

## Next Phase

→ [Phase 6: Documentation & CI/CD](phase-6-docs-and-ci.md)