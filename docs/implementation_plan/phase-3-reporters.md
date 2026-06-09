# Phase 3: Reporters — Output System

> Build the reporting layer: a Rich terminal reporter, a JSON reporter, and an
> HTML reporter. Each implements a common interface so adding new formats is
> trivial.

## Step 3.1 — Abstract Base Reporter (`reporters/base.py`)

**Goal:** Define the reporter contract.

- [x] Create `BaseReporter` abstract class:
  ```python
  class BaseReporter(ABC):
      format_name: str  # e.g. "terminal", "json", "html"

      @abstractmethod
      def report(self, result: CheckReport, output: Path | None = None) -> str:
          """
          Generate a report from check results.

          Args:
              result: The check result to report on.
              output: Optional file path to write to. If None, return as string.

          Returns:
              The formatted report as a string.
          """
          ...
  ```
- [x] Add `report_to_console(self, result: CheckReport) -> None` default method:
  - Calls `self.report(result)` and prints to stdout
  - Subclasses can override for special console handling (e.g., Rich live output)

**Acceptance:** `BaseReporter` cannot be instantiated; subclasses that implement `report()` can.

---

## Step 3.2 — Reporter Factory (`reporters/__init__.py`)

**Goal:** Create a factory to get the right reporter by name.

- [x] Create `get_reporter(format_name: str) -> BaseReporter`:
  - `"terminal"` → `TerminalReporter`
  - `"json"` → `JSONReporter`
  - `"html"` → `HTMLReporter`
  - Raise `ValueError` for unknown formats
- [x] Create `list_formats() -> list[str]` — returns `["terminal", "json", "html"]`
- [x] Register reporters via import (no manual mapping — each reporter registers itself)

**Acceptance:** `get_reporter("json")` returns a `JSONReporter` instance.

---

## Step 3.3 — Terminal Reporter (`reporters/terminal.py`)

**Goal:** Rebuild the colored terminal output using Rich instead of raw ANSI codes.

- [x] Create `TerminalReporter(BaseReporter)`:
  - `format_name = "terminal"`
- [x] Implement `report()`:
  - Build a Rich `Table` for the summary header (file name, date, score)
  - Group issues by severity: CRITICAL (red), WARNING (yellow), OK (green)
  - Each Issue renders as a `rich.panel.Panel` or table row with:
    - Icon (🔴 / 🟡 / 🟢 or Rich equivalents)
    - Severity label with color
    - Title in bold
    - Detail in dim text
    - Remediation in italic (if present)
    - Location badge (if present)
  - Footer with overall verdict:
    - CRITICAL issues → "✗ NOT ATS-FRIENDLY" in red
    - Only warnings → "⚠ LIKELY ATS-COMPATIBLE" in yellow
    - All OK → "✓ ATS-FRIENDLY" in green
- [x] Implement `report_to_console()`:
  - Use `rich.console.Console` for actual terminal output
  - Detect terminal color support; fall back gracefully if no color
- [x] Add `--no-color` support via config (`config.color_output`)
- [x] Add `--verbose` mode via config:
  - Normal: show only CRITICAL and WARNING
  - Verbose: show all including OK
- [ ] Add progress bar during check using `rich.progress` (Note: Moved to Engine/CLI concern as reporters process the final report)

**Acceptance:** Output is visually equivalent to the original ANSI-based report but uses Rich for better rendering (tables, panels, proper width handling). Falls back gracefully in non-TTY environments.

---

## Step 3.4 — JSON Reporter (`reporters/json_reporter.py`)

**Goal:** Produce machine-readable JSON output for integration with other tools.

- [ ] Create `JSONReporter(BaseReporter)`:
  - `format_name = "json"`
- [ ] Implement `report()`:
  - Serialize `CheckReport` to JSON using Pydantic's `.model_dump_json()`
  - Include all fields:
    ```json
    {
      "pdf_path": "resume.pdf",
      "timestamp": "2025-01-15T10:30:00Z",
      "score": 72.5,
      "summary": {
        "critical_count": 2,
        "warning_count": 3,
        "ok_count": 5
      },
      "checks": [
        {
          "checker": "file_size",
          "execution_time_ms": 1.2,
          "issues": [
            {
              "severity": "critical",
              "title": "File too large",
              "detail": "...",
              "remediation": "...",
              "location": "Entire document"
            }
          ]
        }
      ]
    }
    ```
  - Pretty-print by default (indent=2)
  - Add `--compact` flag support for minified output
- [ ] Write to file if `output` path is provided

**Acceptance:** `JSONReporter().report(result)` produces valid, parseable JSON. Round-trip `CheckReport.model_validate_json(json_str)` recovers the original data.

---

## Step 3.5 — HTML Reporter (`reporters/html_reporter.py`)

**Goal:** Produce a self-contained HTML report that can be shared or archived.

- [x] Create `HTMLReporter(BaseReporter)`:
  - `format_name = "html"`
- [x] Implement `report()`:
  - Generate a self-contained HTML file with embedded CSS (no external dependencies)
  - Use semantic HTML structure:
    - `<header>` with file name and timestamp
    - `<section class="summary">` with score and counts
    - `<section class="critical">`, `<section class="warning">`, `<section class="ok">`
    - Each issue as a `<div class="issue">` with severity icon, title, detail, remediation
  - Responsive CSS: works on mobile
  - Print-friendly CSS: `@media print` rules
  - Color scheme matching terminal output (red/yellow/green severity)
  - Include a "Exported from ATS Resume Checker" footer with version
- [x] Use Python's built-in `html` module for escaping (security: prevent XSS from PDF content)
- [x] Write to file if `output` path is provided

**Acceptance:** HTML report opens in a browser, is readable, and looks professional. No external CSS/JS dependencies.

---

## Step 3.6 — Extracted Text Reporter (sidecar file)

**Goal:** Move the `.extracted.txt` sidecar generation from the checker to a reporter concern.

- [x] Create `save_extracted_text(result: CheckReport, pdf_path: Path) -> Path`:
  - Writes `CheckReport.all_text` (from text extraction checker) to `{stem}.extracted.txt`
  - Only writes if text extraction checker ran and found text
  - This is not a full reporter class — it's a utility called by the terminal reporter
- [x] Add `--save-text` CLI flag (deferred to Phase 4, but add the function now)

**Acceptance:** Calling `save_extracted_text()` creates the sidecar file matching original behavior.

---

## Dependencies

- **Phase 1** (models — `CheckReport`, `Issue`, `Severity`)
- **Phase 2** (engine — to produce `CheckReport` objects)

## Next Phase

→ [Phase 4: CLI & Configuration](phase-4-cli-and-config.md)