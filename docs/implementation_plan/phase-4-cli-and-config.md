# Phase 4: CLI Interface & Configuration

> Build the command-line interface using Typer, add configuration file support,
> and enable batch processing of multiple resumes.

## Step 4.1 — CLI App Shell (`cli.py`)

**Goal:** Create the Typer CLI app with the main `check` command.

- [x] Create `app = typer.Typer()` with:
  - Name: `ats-check`
  - Help text: "Check PDF resumes for ATS compatibility issues"
  - Rich markup enabled
- [x] Create `check` command:
  ```python
  @app.command()
  def check(
      paths: list[Path] = typer.Argument(
          ..., exists=True, help="PDF file(s) to check"
      ),
      format: str = typer.Option(
          "terminal", "--format", "-f",
          help="Output format: terminal, json, html"
      ),
      output: Path | None = typer.Option(
          None, "--output", "-o",
          help="Output file path (required for json/html format)"
      ),
      checker: list[str] | None = typer.Option(
          None, "--checker", "-c",
          help="Run only these checkers (by name)"
      ),
      skip_checker: list[str] | None = typer.Option(
          None, "--skip-checker", "-s",
          help="Skip these checkers (by name)"
      ),
      config_file: Path | None = typer.Option(
          None, "--config",
          help="Path to configuration file"
      ),
      verbose: bool = typer.Option(
          False, "--verbose", "-v",
          help="Show all checks including passing ones"
      ),
      no_color: bool = typer.Option(
          False, "--no-color",
          help="Disable colored output"
      ),
      save_text: bool = typer.Option(
          False, "--save-text",
          help="Save extracted text as .extracted.txt sidecar file"
      ),
      score: bool = typer.Option(
          False, "--score",
          help="Calculate and show ATS compatibility score"
      ),
  ) -> None:
  ```
- [x] Validate inputs:
  - Each path must be a `.pdf` file
  - If `format` is `json` or `html` and `output` is None and multiple paths given → error
  - Unknown checker names → error with list of valid names
- [x] Load config (merge defaults → file → env vars → CLI flags)
- [x] Run check via `run_check()`
- [x] Implement progress bar during check using `rich.progress` in the CLI/Engine loop
- [x] Report via appropriate reporter
- [x] Handle `KeyboardInterrupt` gracefully (print "Aborted.")
- [x] Exit code: 0 if no critical issues, 1 if critical issues, 2 for errors

**Acceptance:** `ats-check check resume.pdf` runs all checks and prints a terminal report. `ats-check check resume.pdf --format json -o report.json` writes JSON.

---

## Step 4.2 — List Checkers Command

**Goal:** Add a command to list available checkers.

- [x] Create `list-checkers` command:
  ```python
  @app.command("list-checkers")
  def list_checkers() -> None:
      """List all available checker modules and their descriptions."""
  ```
- [x] Output a Rich table:
  ```
  Name              Description
  ─────────────────────────────────────────────────────────
  file_size         Checks PDF file size against portal limits
  images            Detects embedded images ATS cannot read
  text_extraction   Verifies text can be cleanly extracted
  ...
  ```
- [x] This helps users know valid values for `--checker` and `--skip-checker`

**Acceptance:** `ats-check list-checkers` prints all registered checkers.

---

## Step 4.3 — Configuration File Support

**Goal:** Allow users to customize behavior via config files.

- [x] Define config file search order:
  1. `--config` CLI flag (highest priority)
  2. `ats-checker.toml` in current directory
  3. `~/.config/ats-checker/config.toml` (XDG-style)
  4. Built-in defaults (lowest priority)
- [x] Support TOML format (most Pythonic):
  ```toml
  [thresholds]
  max_file_size_kb = 1024
  warning_file_size_kb = 500
  min_text_length = 50

  [sections]
  experience = ["experience", "work experience", "employment"]
  education = ["education", "academic", "qualifications"]
  skills = ["skills", "technical skills", "core competencies"]

  [output]
  default_format = "terminal"
  color = true
  ```
- [x] Merge config layers: defaults ← file ← env vars ← CLI flags
- [x] Validate merged config (e.g., warning threshold < critical threshold)
- [x] Print effective config with `--show-config` flag (for debugging)

**Acceptance:** `ats-check check resume.pdf --config my-config.toml` loads and applies custom config. Config values override defaults.

---

## Step 4.4 — Batch Processing

**Goal:** Check multiple PDF files in one invocation.

- [x] Support multiple `paths` arguments:
  - `ats-check check resume1.pdf resume2.pdf resume3.pdf`
  - `ats-check check ./resumes/*.pdf`
- [x] For terminal format: print each report with a separator
- [x] For JSON format: output a single JSON array or individual files
- [x] For HTML format: generate a single HTML report with sections per file
- [x] Show summary across all files: "3 checked, 1 critical, 1 warning, 1 passed"
- [x] Exit code: 1 if ANY file has critical issues, 0 if all pass

**Acceptance:** `ats-check check *.pdf --format terminal` checks all PDFs and shows individual + summary reports.

---

## Step 4.5 — `__main__.py` Entry Point

**Goal:** Support `python -m ats_checker` invocation.

- [x] Create `src/ats_checker/__main__.py`:
  ```python
  from ats_checker.cli import app

  if __name__ == "__main__":
      app()
  ```
- [x] Verify both invocation methods work:
  - `ats-check check resume.pdf`
  - `python -m ats_checker check resume.pdf`

**Acceptance:** Both invocation methods produce identical output.

---

## Step 4.6 — Error Handling & Edge Cases

**Goal:** Handle all user-facing error cases gracefully.

- [ ] File not found → clear error message, exit code 2
- [ ] Not a PDF → clear error message, exit code 2
- [ ] Corrupted PDF → `PDFCorruptedError` caught, clear message
- [ ] Password-protected PDF → `PDFPasswordError` caught, clear message
- [ ] Empty PDF → warning, not crash
- [ ] No checkers selected (all skipped) → error message
- [ ] Invalid config file → clear error with line number
- [ ] Output directory doesn't exist → offer to create or error
- [ ] Permission denied on output file → clear message
- [ ] Unicode in file paths → handled correctly on Windows

**Acceptance:** All error cases produce clear, actionable messages. No stack traces leak to users.

---

## Dependencies

- **Phase 1** (models, config)
- **Phase 2** (engine, checker registry)
- **Phase 3** (reporters)

## Next Phase

→ [Phase 5: Testing](phase-5-testing.md)