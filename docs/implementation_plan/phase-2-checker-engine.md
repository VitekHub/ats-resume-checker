# Phase 2: Checker Engine — Modular Plugin Architecture

> Refactor every check from `ats_check.py` into its own module with a common
> interface. Build a registry system so new checkers can be added with zero
> changes to core code.

## Step 2.1 — Abstract Base Checker (`checkers/base.py`)

**Goal:** Define the contract every checker must follow.

- [x] Create `BaseChecker` abstract class:
  ```python
  class BaseChecker(ABC):
      name: str                    # unique identifier, e.g. "file_size"
      description: str             # one-line human description
      severity_on_fail: Severity   # default severity if check fails

      def __init__(self, config: Config) -> None:
          self.config = config

      @abstractmethod
      def check(self, pdf: PDFDocument) -> list[Issue]:
          """Run this checker against the PDF and return any issues found."""
          ...
  ```
- [x] Add `__repr__` returning `f"<{self.__class__.__name__} name={self.name}>"`
- [x] Add `__str__` returning `self.name`
- [x] Add a class-level `requires_text: bool = True` flag — if `True`, the engine
      pre-loads extracted text before calling `check()`. Checkers that don't need
      text (e.g., file_size) can set `requires_text = False` to skip extraction.
- [x] Ensure all abstract methods have docstrings explaining parameters and return type

**Acceptance:** `BaseChecker` cannot be instantiated; subclasses that implement `check()` can.

---

## Step 2.2 — Checker Registry (`checkers/registry.py`)

**Goal:** Create a discovery and registration system for checkers.

- [x] Create `CheckerRegistry` class:
  - `register(checker_class: type[BaseChecker]) -> None` — decorator or method
  - `get(name: str) -> type[BaseChecker]` — retrieve by name
  - `get_all() -> list[type[BaseChecker]]` — return all registered
  - `get_default() -> list[type[BaseChecker]]` — return the standard set
- [x] Provide `@register_checker` decorator:
  ```python
  @register_checker
  class FileSizeChecker(BaseChecker):
      ...
  ```
- [x] Auto-discovery: import all modules in `checkers/` package so decorators fire
- [x] Support `--checker` / `--skip-checker` CLI overrides (deferred to Phase 4,
      but registry must support building a subset list by name)
- [x] Add `__all__` export in `checkers/__init__.py`

**Acceptance:** Registering a checker and retrieving it by name works. Listing all registered checkers returns the full set.

---

## Step 2.3 — File Size Checker (`checkers/file_size.py`)

**Goal:** Port `check_file_size()` to the new architecture.

- [x] Create `FileSizeChecker(BaseChecker)`:
  - `name = "file_size"`
  - `description = "Checks PDF file size against common portal upload limits"`
  - `requires_text = False`
- [x] Implement `check()`:
  - Get `file_size_kb` from `PDFDocument`
  - Compare against `config.max_file_size_kb` (critical) and `config.warning_file_size_kb` (warning)
  - Return `[Issue]` list
- [x] All thresholds come from config, no hard-coded values
- [x] Add `remediation` field to each Issue with actionable advice
- [x] Add `location` field (e.g., `"Entire file"`)

**Acceptance:** Running `FileSizeChecker(config).check(pdf)` produces the same logical results as the original `check_file_size()` for the same inputs.

---

## Step 2.4 — Images Checker (`checkers/images.py`)

**Goal:** Port `check_images()` to the new architecture.

- [x] Create `ImagesChecker(BaseChecker)`:
  - `name = "images"`
  - `description = "Detects embedded images that ATS cannot read"`
  - `requires_text = False`
- [x] Implement `check()`:
  - Use `PDFDocument` image extraction helpers
  - Classify images as large (> `config.large_image_px`) or small
  - Return Issues for large images (CRITICAL), small images (WARNING)
  - Return OK Issue if no images found
- [x] Add `remediation` to each Issue (e.g., "Remove portrait photo or convert to plain text")
- [x] Add `location` (e.g., "Page 2")

**Acceptance:** Produces equivalent results to original `check_images()`, but via `PDFDocument` API.

---

## Step 2.5 — Text Extraction Checker (`checkers/text_extraction.py`)

**Goal:** Port `check_text_extraction()` to the new architecture.

- [x] Create `TextExtractionChecker(BaseChecker)`:
  - `name = "text_extraction"`
  - `description = "Verifies text can be cleanly extracted in reading order"`
  - `requires_text = True`
- [x] Implement `check()`:
  - Use pre-loaded text from `PDFDocument`
  - Check `text_length < config.min_text_length` → CRITICAL
  - Check `alpha_ratio < config.warning_alpha_ratio` → CRITICAL or WARNING
  - Check `alpha_ratio < config.min_alpha_ratio` → WARNING
  - Otherwise → OK
  - Remove the side effect of writing `.extracted.txt` (that's a reporter concern)
- [x] Add `remediation` with advice about using text-based PDFs, avoiding scanned images

**Acceptance:** Produces equivalent severity results. No file I/O side effects.

---

## Step 2.6 — Layout Checker (`checkers/layout.py`)

**Goal:** Port `check_columns_and_tables()` to the new architecture.

- [x] Create `LayoutChecker(BaseChecker)`:
  - `name = "layout"`
  - `description = "Detects multi-column layouts and tables that scramble ATS text order"`
  - `requires_text = True` (needs word positions)
- [x] Implement `check()`:
  - Table detection using `pdfplumber` page tables
  - Multi-column detection using word X-position clustering
  - Use `config.column_gap_threshold` and `config.min_words_for_column_check`
  - Include page number in `location` field
- [x] Add `remediation`: "Use single-column layout. Replace tables with section headers and bullet points."

**Acceptance:** Produces equivalent results to `check_columns_and_tables()`.

---

## Step 2.7 — Sections Checker (`checkers/sections.py`)

**Goal:** Port section detection logic (minus contact info) to the new architecture.

- [x] Create `SectionsChecker(BaseChecker)`:
  - `name = "sections"`
  - `description = "Checks for standard resume sections that ATS parsers expect"`
  - `requires_text = True`
- [x] Implement `check()`:
  - Use `config.expected_sections` for the section → keywords mapping
  - Search for each section's keywords in extracted text
  - Report missing sections as WARNING
  - Report found sections as OK
- [x] Separate from contact info (which moves to its own checker)
- [x] Add `remediation`: "Use standard section headers like Experience, Education, Skills."

**Acceptance:** Correctly detects section headers using config-defined keywords.

---

## Step 2.8 — Contact Info Checker (`checkers/contact_info.py`)

**Goal:** Extract contact info detection from the original `check_sections()` into its own checker.

- [x] Create `ContactInfoChecker(BaseChecker)`:
  - `name = "contact_info"`
  - `description = "Detects email and phone number in the resume text"`
  - `requires_text = True`
- [x] Implement `check()`:
  - Missing email → CRITICAL
  - Missing phone → WARNING
  - Both present → OK
- [x] Add `remediation`: "Add your email as plain text, not in an image or special font."

**Acceptance:** Email and phone detection matches original logic, but patterns are configurable.

---

## Step 2.9 — Fonts Checker (`checkers/fonts.py`)

**Goal:** Port `check_fonts()` to the new architecture.

- [x] Create `FontsChecker(BaseChecker)`:
  - `name = "fonts"`
  - `description = "Checks for non-standard or symbol fonts that ATS may not render"`
  - `requires_text = False`
- [x] Implement `check()`:
  - Use `PDFDocument` font extraction
  - Compare against `config.safe_fonts` and `config.symbol_fonts`
  - Normalize font names (strip hyphens, spaces, underscores, lowercase)
  - Symbol fonts → CRITICAL
  - Unusual fonts → WARNING (with count)
  - All safe → OK
- [x] Add `remediation`: "Use standard fonts like Arial, Calibri, or Helvetica."

**Acceptance:** Font detection matches original logic. Config-driven safe/symbol font lists.

---

## Step 2.10 — Metadata Checker (`checkers/metadata.py`)

**Goal:** Port `check_metadata()` to the new architecture.

- [x] Create `MetadataChecker(BaseChecker)`:
  - `name = "metadata"`
  - `description = "Checks PDF metadata for personal information leaks"`
  - `requires_text = False`
- [x] Implement `check()`:
  - Use `PDFDocument.metadata` property
  - Check author, subject, creator, producer fields
  - Use `config.software_keywords` to filter out software names
  - Personal info leak → WARNING
  - Clean → OK
- [x] Add `remediation`: "Strip metadata in your PDF editor (File → Properties)."

**Acceptance:** Metadata privacy detection matches original logic.

---

## Step 2.11 — Special Characters Checker (`checkers/special_chars.py`)

**Goal:** Port `check_special_characters()` to the new architecture.

- [x] Create `SpecialCharsChecker(BaseChecker)`:
  - `name = "special_chars"`
  - `description = "Flags unusual Unicode characters that may not parse in ATS"`
  - `requires_text = True`
- [x] Implement `check()`:
  - Check extracted text for characters in problematic Unicode ranges
  - Same ranges as original: General Punctuation, Arrows, Box Drawing,
    Geometric Shapes, Miscellaneous Symbols, Dingbats
  - Consider making ranges configurable in `Config`
  - Sample up to 5 characters per category
  - Issues found → WARNING with character list
  - None found → OK
- [x] Add `remediation`: "Replace Unicode symbols with plain ASCII equivalents (use - instead of —, * instead of •)."

**Acceptance:** Special character detection matches original logic.

---

## Step 2.12 — Check Engine (`engine.py`)

**Goal:** Create the orchestrator that runs all checkers and produces a `CheckReport`.

- [ ] Create `run_check()` function:
  ```python
  def run_check(
      pdf_path: Path,
      config: Config | None = None,
      checkers: list[str] | None = None,  # None = all default checkers
      skip_checkers: list[str] | None = None,
  ) -> CheckReport:
  ```
- [ ] Implementation:
  1. Load config (use defaults if `None`)
  2. Resolve checkers from registry (filter by `checkers`/`skip_checkers`)
  3. Open `PDFDocument` (with context manager)
  4. Run each checker, collect `CheckerResult` per checker
  5. Measure execution time per checker
  6. Assemble `CheckReport`
  7. Return result (no I/O — reporters handle output)
- [ ] Add error handling:
  - If a checker raises an exception, catch it, log warning, and continue
  - Record the error as a CRITICAL Issue in the `CheckerResult`
  - Never let one checker crash the whole check
- [ ] Pre-load text extraction if any checker has `requires_text = True`

**Acceptance:** `run_check(Path("resume.pdf"))` returns a complete `CheckReport` with all checker results.

---

## Dependencies

- **Phase 1** must be complete (models, config, PDF utilities, package structure)

## Next Phase

→ [Phase 3: Reporters](phase-3-reporters.md)