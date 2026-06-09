# ATS Resume Checker — Project Overview & Implementation Plan

## What Is This Project?

**ATS Resume Checker** is a Python tool that analyzes PDF resumes/CVs for compatibility with Applicant Tracking Systems (ATS). ATS software is used by employers to automatically parse and filter job applications — if a resume isn't ATS-friendly, it may be silently rejected regardless of the applicant's qualifications.

The tool checks PDFs for common issues that cause ATS failures: embedded images, garbled text extraction, multi-column layouts, missing sections, non-standard fonts, metadata leaks, and problematic Unicode characters. It produces a clear report with severity-rated findings and actionable recommendations.

## Current State

The project currently exists as a single `ats_check.py` script (~520 lines). It works, but it's a monolith — all logic, models, I/O, and CLI handling in one file. This makes it hard to test, extend, and maintain.

**What works now:**
- File size check
- Image detection (large + small)
- Text extraction quality assessment
- Column/table layout detection
- Section header detection (experience, education, skills)
- Contact info detection (email, phone)
- Font analysis (standard vs. symbol/unusual)
- PDF metadata privacy check
- Special character detection
- Colored terminal report output
- Sidecar `.extracted.txt` file generation

**What needs improvement:**
- No project structure (single-file monolith)
- No type annotations beyond basic hints
- No tests
- No configuration system
- No extensibility (adding a new check means editing the main file)
- Single output format (terminal only)
- No scoring or grade system
- No batch processing
- Hard-coded thresholds and patterns
- No packaging (no `pyproject.toml`)
- ANSI colors baked into business logic

## Goals for the Rebuild

1. **Modular architecture** — each checker in its own module, pluggable registry
2. **Testable** — full unit + integration test coverage
3. **Extensible** — add new checkers without touching core code
4. **Professional packaging** — `pyproject.toml`, proper entry points, type hints
5. **Multiple output formats** — terminal (Rich), JSON, HTML
6. **Configurable** — thresholds, sections, patterns adjustable via config
7. **Well-documented** — API docs, user guide, inline docstrings
8. **CI/CD ready** — linting, type checking, testing in automation
9. **Scoring system** — overall ATS compatibility score with breakdown
10. **Batch processing** — check multiple resumes at once
11. **Max 300 lines per file** — no source file should exceed 300 lines; if a file grows beyond that, split it into smaller, focused modules

## Implementation Phases

| Phase | File | Description |
|-------|------|-------------|
| 1 | [phase-1-foundation.md](phase-1-foundation.md) | Project structure, models, configuration, packaging |
| 2 | [phase-2-checker-engine.md](phase-2-checker-engine.md) | Refactor all checkers into modular plugins |
| 3 | [phase-3-reporters.md](phase-3-reporters.md) | Output system — terminal (Rich), JSON, HTML reporters |
| 4 | [phase-4-cli-and-config.md](phase-4-cli-and-config.md) | CLI interface, configuration files, batch mode |
| 5 | [phase-5-testing.md](phase-5-testing.md) | Unit tests, integration tests, fixtures, coverage |
| 6 | [phase-6-docs-and-ci.md](phase-6-docs-and-ci.md) | Documentation, CI/CD pipeline, pre-commit hooks |
| 7 | [phase-7-advanced-features.md](phase-7-advanced-features.md) | Scoring, suggestions, comparison, caching |

## Target Tech Stack

| Category | Choice | Rationale |
|----------|--------|-----------|
| Language | Python 3.11+ | Modern type hints, `match` statements, performance |
| CLI | [Typer](https://typer.tiangolo.com/) | Type-safe CLI with auto-generated help |
| Terminal output | [Rich](https://rich.readthedocs.io/) | Beautiful tables, markdown, progress bars |
| PDF text | [pdfplumber](https://github.com/jsvine/pdfplumber) | Best text extraction order |
| PDF structure | [PyMuPDF](https://pymupdf.readthedocs.io/) | Images, fonts, metadata access |
| Configuration | [Pydantic Settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/) | Type-safe config with env var support |
| Testing | [pytest](https://docs.pytest.org/) + [pytest-cov](https://pytest-cov.readthedocs.io/) | Standard Python testing |
| Type checking | [mypy](http://mypy-lang.org/) | Static type analysis |
| Linting | [Ruff](https://docs.astral.sh/ruff/) | Fast linter + formatter (replaces flake8, isort, black) |
| Packaging | [Hatch](https://hatch.pypa.io/) or [setuptools](https://setuptools.pypa.io/) | Build system via `pyproject.toml` |

## Target Project Structure

```
ats-resume-checker/
├── pyproject.toml
├── README.md                    # Project README (separate from plan README)
├── LICENSE
├── docs/
│   └── implementation_plan/     # ← this plan
│       ├── README.md
│       ├── overview.md
│       ├── phase-1-foundation.md
│       ├── phase-2-checker-engine.md
│       ├── phase-3-reporters.md
│       ├── phase-4-cli-and-config.md
│       ├── phase-5-testing.md
│       ├── phase-6-docs-and-ci.md
│       └── phase-7-advanced-features.md
├── src/
│   └── ats_checker/
│       ├── __init__.py
│       ├── __main__.py           # python -m ats_checker
│       ├── cli.py                # Typer CLI app
│       ├── config.py             # Pydantic Settings configuration
│       ├── models.py             # Issue, CheckerResult, Severity, etc.
│       ├── scoring.py            # ATS compatibility score calculation
│       ├── engine.py             # Orchestrates checker pipeline
│       ├── checkers/             # One module per checker
│       │   ├── __init__.py
│       │   ├── base.py           # Abstract BaseChecker
│       │   ├── registry.py       # Checker discovery and registration
│       │   ├── file_size.py
│       │   ├── images.py
│       │   ├── text_extraction.py
│       │   ├── layout.py         # columns + tables
│       │   ├── sections.py
│       │   ├── fonts.py
│       │   ├── metadata.py
│       │   ├── special_chars.py
│       │   └── contact_info.py   # Extracted from sections.py
│       ├── reporters/            # One module per output format
│       │   ├── __init__.py
│       │   ├── base.py           # Abstract BaseReporter
│       │   ├── terminal.py       # Rich-based terminal output
│       │   ├── json_reporter.py
│       │   └── html_reporter.py
│       └── pdf_utils.py          # Shared PDF loading, caching, helpers
├── tests/
│   ├── conftest.py               # Shared fixtures
│   ├── test_models.py
│   ├── test_engine.py
│   ├── test_config.py
│   ├── test_scoring.py
│   ├── checkers/
│   │   ├── test_file_size.py
│   │   ├── test_images.py
│   │   ├── test_text_extraction.py
│   │   ├── test_layout.py
│   │   ├── test_sections.py
│   │   ├── test_fonts.py
│   │   ├── test_metadata.py
│   │   ├── test_special_chars.py
│   │   └── test_contact_info.py
│   ├── reporters/
│   │   ├── test_terminal.py
│   │   ├── test_json_reporter.py
│   │   └── test_html_reporter.py
│   └── fixtures/
│       ├── clean_resume.pdf
│       ├── scanned_image.pdf
│       ├── multicolumn.pdf
│       ├── unusual_fonts.pdf
│       └── metadata_leak.pdf
└── .github/
    └── workflows/
        └── ci.yml
```