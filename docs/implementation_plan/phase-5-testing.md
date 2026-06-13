# Phase 5: Testing

> Build a comprehensive test suite: unit tests for every checker, integration
> tests for the full pipeline, fixtures for edge cases, and coverage targets.

## Testing Rules

### What TO Test

| # | Rule | Rationale |
|---|------|-----------|
| R1 | **Test behavior, not implementation.** Assert inputs → outputs, not internal variable states. | Implementation tests break on refactors; behavior tests survive them. |
| R2 | **Test boundary conditions and edge cases.** Empty, minimal, maximal, off-by-one, malformed. | Boundaries are where bugs hide. |
| R3 | **Test every public method and model validation rule.** Private helpers are covered transitively. | Public surface = contract; testing internals is redundant. |
| R4 | **Use `pytest.raises` for error/exception paths.** Don't just test the happy path. | Unhandled errors are the #1 source of production bugs. |
| R5 | **Use `@pytest.mark.parametrize` for multi-input scenarios** instead of looping assertions inside one test. | Better failure isolation and readability. |
| R6 | **Integration tests should test the wiring, not re-test unit logic.** | Re-testing what units already proved is waste. |
| R7 | **Mock/patch external dependencies** (filesystem, network, heavy libraries). | Tests must be fast, deterministic, and isolated. |
| R8 | **Test that config overrides actually reach the code that uses them.** | A config path not wired end-to-end is a silently-ignored setting. |

### What NOT to Test

| # | Rule | Rationale |
|---|------|-----------|
| X1 | **Don't test Pydantic/Python built-ins.** No test for "a dict has keys" or "an enum value equals its string." | Trust the framework; test your validation, not its. |
| X2 | **Don't test trivial computed properties** that are just `len(self.list)` or `sum()`. | Unless there's non-obvious logic, it's testing Python. |
| X3 | **Don't test third-party library behavior.** pdfplumber returning text, Rich rendering colors, etc. | That's the library's job; mock it or trust it. |
| X4 | **Don't test `__str__` / `__repr__`** unless the format is a public API contract. | Cosmetic output changes constantly. |
| X5 | **Don't duplicate tests across unit and integration layers.** | Integration tests that re-assert unit-level logic are maintenance burden without added confidence. |
| X6 | **Don't test what a linter/type-checker already catches.** | mypy already validates type contracts. |

---

## Step 5.1 — Test Infrastructure Setup

**Goal:** Set up pytest, fixtures, and test helpers.

- [x] Create `tests/conftest.py` with shared fixtures:
  - `sample_config()` — returns a `Config` with test defaults ✅
  - `clean_pdf()` — returns a `PDFDocument` for a well-formed resume ✅
  - `scanned_pdf()` — returns a `PDFDocument` for a scanned image PDF ✅
  - `multicolumn_pdf()` — returns a `PDFDocument` for a two-column resume ✅
  - `empty_pdf()` — returns a `PDFDocument` for a PDF with no text ✅
  - `tmp_pdf_path()` — returns a temporary PDF file path ✅
  - Additional: `strict_text_config()`, `lenient_filesize_config()`, `large_file_pdf()`, `metadata_leak_pdf()`, `special_chars_pdf()`, `no_contact_pdf()`, `unusual_fonts_pdf()`, `table_layout_pdf()`, `severity_levels()`, `checker_names()`
- [x] Create `tests/fixtures/` directory with test PDF files ✅
  - Approach: Dynamic generation via PyMuPDF (already a dependency) instead of static binary files.
  - `tests/helpers.py` provides: `create_test_pdf()`, `create_scanned_pdf()`, `create_multicolumn_pdf()`, `create_empty_pdf()`, `create_pdf_with_metadata()`, `create_large_pdf()`, `create_pdf_with_special_chars()`
  - `tests/fixtures/.gitkeep` placeholder created for future static fixtures
- [x] Create `tests/helpers.py` with ✅:
  - `create_test_pdf()` — generates a simple PDF with given text (using PyMuPDF)
  - `create_scanned_pdf()` — generates a PDF that's an image with text baked in
  - `create_multicolumn_pdf()` — generates two-column layout PDF
  - `create_empty_pdf()` — generates blank PDF
  - `create_pdf_with_metadata()` — generates PDF with custom metadata
  - `create_large_pdf()` — generates PDF exceeding size thresholds
  - `create_pdf_with_special_chars()` — generates PDF with Unicode special chars
  - `save_test_pdf()` — utility to save PDF bytes to file
  - `assert_issue()` — helper to assert Issue severity, title, checker, detail
  - `assert_issues_contains()` — helper to search issues by severity/title/count
- [x] Add `pytest.ini_options` configuration in `pyproject.toml` ✅:
  - `testpaths = ["tests"]` (already existed)
  - `python_files = ["test_*.py"]` (added)
  - `python_functions = ["test_*"]` (added)
  - `addopts = "--tb=short -q"` (added)

**Acceptance:** `pytest` discovers and runs all tests. Fixtures load correctly.

---

## Step 5.2 — Model Validation Tests (`tests/test_models.py`)

**Goal:** Test custom validation rules and error paths in data models — not framework guarantees.

- [ ] Test `Issue` validation:
  - Empty title raises validation error
  - Invalid severity string raises validation error
- [ ] Test `CheckerResult` computed properties with non-trivial logic:
  - `all_issues` flattens correctly when results have mixed severities
  - `critical_count` / `warning_count` / `ok_count` computed correctly (only if logic is non-trivial)
- [ ] Test `CheckReport` flattening:
  - `all_issues` merges issues from multiple `CheckerResult`s correctly
  - Counts are consistent with flattened list
- [ ] Test `Config` validation rules (from `config.py`):
  - `warning_file_size_kb > max_file_size_kb` → validation error
  - `min_text_length < 0` → validation error
  - Empty `expected_sections` → validation error
  - Invalid severity string → validation error

> **Note (X1):** Skip tests for Pydantic defaults (`None`, required fields), enum membership,
> `__str__` format, `timestamp = now()` defaults — those are framework guarantees.

**Acceptance:** All model validation tests pass. Custom validation rules are enforced.

---

## Step 5.3 — Configuration Tests (`tests/test_config.py`)

**Goal:** Test configuration loading, merging, and custom validation — not default values.

- [ ] Test config from TOML file:
  - Load a partial TOML config → missing keys use defaults
  - Load a full TOML config → all values overridden
- [ ] Test config from environment variables:
  - `ATS_CHECKER_MAX_FILE_SIZE_KB=2048` → override works
- [ ] Test config merging priority:
  - Defaults ← file ← env vars ← CLI → each layer overrides correctly
- [ ] Test config validation (custom rules only):
  - `warning_file_size_kb > max_file_size_kb` → validation error
  - `min_text_length < 0` → validation error
  - Empty `expected_sections` → validation error
- [ ] Test config reaches checkers (R8):
  - A checker with custom threshold via config → behaves according to that threshold
  - A checker with env-var override → behaves according to that override

> **Note (X1):** Skip "all default values are sensible" and "`Config()` with no arguments works" —
> those are Pydantic Settings behavior.

**Acceptance:** Config tests pass for all merging and validation scenarios. Config values reach checkers.

---

## Step 5.4 — PDF Utilities Tests (`tests/test_pdf_utils.py`)

**Goal:** Test our error handling, caching, and normalization logic — not third-party extraction.

- [ ] Test `PDFDocument` error handling:
  - Raises `PDFCorruptedError` for corrupted files
  - Raises appropriate error for non-existent files
  - Context manager closes resources even on exception
- [ ] Test `extract_text()` caching:
  - Second call doesn't re-extract (mock the underlying extractor, assert called once)
- [ ] Test `extract_text()` normalization (our layer):
  - Whitespace normalization, encoding fixes, or other post-processing we add
- [ ] Test `extract_images_info()` classification logic:
  - Large vs small image classification works correctly
- [ ] Test `extract_font_info()` normalization logic:
  - Font names are normalized (strip prefixes, lowercase, etc.)
  - Empty set returned for image-only PDFs (test our fallback, not pdfplumber)

> **Note (X3):** Skip tests for "opens valid PDF without error," `page_count`,
> `file_size_kb`, "returns all text from multi-page PDF," "returns word list" —
> those are thin wrappers over pdfplumber/PyMuPDF. Test our logic layer, not theirs.

**Acceptance:** All PDF utility error handling and normalization tests pass.

---

## Step 5.5 — Checker Unit Tests

**Goal:** Test each checker in isolation with controlled inputs.

### `tests/checkers/test_file_size.py`
- [ ] Small file (< 500 KB) → OK
- [ ] Medium file (500–1024 KB) → WARNING
- [ ] Large file (> 1024 KB) → CRITICAL
- [ ] Custom thresholds in config override defaults (R8)

### `tests/checkers/test_images.py`
- [ ] PDF with no images → OK
- [ ] PDF with large images → CRITICAL
- [ ] PDF with small images only → WARNING
- [ ] PDF with both → both issues reported
- [ ] Image classification threshold from config is respected (R8)

### `tests/checkers/test_text_extraction.py`
- [ ] Good text extraction → OK
- [ ] Very short text (< 50 chars) → CRITICAL
- [ ] Low alpha ratio (< 0.4) → CRITICAL (garbled)
- [ ] Medium alpha ratio (0.4–0.6) → WARNING
- [ ] High alpha ratio (> 0.6) → OK
- [ ] Custom thresholds respected (R8)
- [ ] Use `@pytest.mark.parametrize` for alpha ratio thresholds (R5)

### `tests/checkers/test_layout.py`
- [ ] Single-column layout → OK
- [ ] Two-column layout → WARNING
- [ ] Table layout → WARNING
- [ ] PDF with few words (< `min_words_for_column_check`) → skip column check
- [ ] Config threshold for column detection is respected (R8)

### `tests/checkers/test_sections.py`
- [ ] All sections present → OK
- [ ] Missing "experience" → WARNING
- [ ] Missing "education" → WARNING
- [ ] Custom section definitions in config (R8)
- [ ] Case-insensitive section matching

### `tests/checkers/test_contact_info.py`
- [ ] Email + phone present → OK
- [ ] Missing email → CRITICAL
- [ ] Missing phone → WARNING
- [ ] Various phone formats (US, Czech, international) — use `@pytest.mark.parametrize` (R2, R5)
- [ ] Custom regex patterns in config (R8)

### `tests/checkers/test_fonts.py`
- [ ] All safe fonts → OK
- [ ] Symbol font (Wingdings) → CRITICAL
- [ ] Unusual fonts → WARNING
- [ ] Mixed safe and unsafe → WARNING
- [ ] Custom safe/symbol font lists in config (R8)

### `tests/checkers/test_metadata.py`
- [ ] Clean metadata → OK
- [ ] Personal name in author field → WARNING
- [ ] Software name in creator field → OK (not flagged)
- [ ] Multiple sensitive fields → single WARNING (deduplication)

### `tests/checkers/test_special_chars.py`
- [ ] No special characters → OK
- [ ] Em dash (U+2014) → WARNING
- [ ] Bullet (U+2022) → WARNING
- [ ] Box drawing chars → WARNING
- [ ] Multiple categories → single WARNING with details (deduplication)

**Acceptance:** All checker unit tests pass. Each checker is tested in isolation.

---

## Step 5.6 — Engine Integration Tests (`tests/test_engine.py`)

**Goal:** Test the full check pipeline end-to-end — wiring, not re-tested unit logic.

- [ ] Test `run_check()` with a clean PDF:
  - Returns `CheckReport` with results for all checkers
  - No CRITICAL issues
- [ ] Test `run_check()` with a problematic PDF:
  - Returns CRITICAL and WARNING issues
  - All checkers ran (check checker names in results)
- [ ] Test `run_check()` with `checkers` filter:
  - Only specified checkers run
  - `CheckReport.check_results` has only those checkers
- [ ] Test `run_check()` with `skip_checkers`:
  - Specified checkers are skipped
  - Others still run
- [ ] Test error handling:
  - A checker that raises an exception → caught, recorded as CRITICAL issue, others continue
- [ ] Test `requires_text=False` optimization:
  - When only `requires_text=False` checkers are selected, text extraction is not called
  - Verify by mocking `extract_text` and asserting it was not called

> **Note (R1):** The `requires_text` optimization test should verify *observable behavior*
> (text extraction not called) not implementation details (internal flag checks).
> **Note (X5):** Don't re-assert specific severity levels already covered in checker unit tests.
> Focus on "all checkers ran" and "error resilience."

**Acceptance:** Full pipeline tests pass. Error handling is robust.

---

## Step 5.7 — Reporter Tests

### `tests/reporters/test_terminal.py`
- [ ] Output contains all issue titles (behavior, not formatting)
- [ ] `--verbose` flag includes OK issues in output
- [ ] Non-verbose mode omits OK issues
- [ ] Severity-to-style mapping is correct (mock Rich, assert we call the right style)
- [ ] `--no-color` passes the flag through to Rich (not testing Rich's stripping)

> **Note (X3):** Don't test that Rich produces red/yellow/green ANSI codes — that's testing Rich.
> Test our severity → style mapping instead.

### `tests/reporters/test_json_reporter.py`
- [ ] Output is valid JSON (parseable, correct schema)
- [ ] All required fields present (checker names, severities, details)
- [ ] File output works when `output` path is provided
- [ ] Round-trip only if JSON reporter transforms/filters data; skip if it's a plain `model_dump_json()` (X1)

### `tests/reporters/test_html_reporter.py`
- [ ] Output is valid HTML (parseable)
- [ ] No XSS vulnerabilities — PDF content is HTML-escaped (R4)
- [ ] Contains all issue titles and details
- [ ] File output works when `output` path is provided
- [ ] Template is loaded correctly (snapshot or structure test, not string-contains for CSS)

> **Note (X2):** Don't test "Print CSS present" with `assert "css" in output` —
> use a snapshot test or test the template loading logic instead.

**Acceptance:** All reporter tests pass. Output formats are correct and safe.

---

## Step 5.8 — CLI Integration Tests (`tests/test_cli.py`)

**Goal:** Test the CLI interface end-to-end — flag wiring and exit codes, not re-tested logic.

- [ ] `ats-check check resume.pdf` → runs and exits 0 for clean PDF
- [ ] `ats-check check problematic.pdf` → runs and exits 1
- [ ] `ats-check check nonexistent.pdf` → exits 2 with error
- [ ] `ats-check check resume.pdf --format json -o out.json` → creates JSON file
- [ ] `ats-check check resume.pdf --format html -o out.html` → creates HTML file
- [ ] `ats-check check resume.pdf --checker file_size --checker images` → runs only those checkers
- [ ] `ats-check check resume.pdf --skip-checker fonts` → skips fonts
- [ ] `ats-check list-checkers` → lists all checker names
- [ ] `ats-check check resume.pdf --config custom.toml` → config flag reaches engine (R8)

> **Note (X5):** Don't re-test `--verbose` showing OK issues or `--no-color` stripping ANSI —
> those are reporter concerns already covered in Step 5.7. CLI tests verify flag plumbing only.

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