# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

ATS Resume Checker — a Python CLI tool that analyzes PDF resumes for ATS (Applicant Tracking System) compatibility. It checks for embedded images, garbled text extraction, problematic layouts, unsafe fonts, missing sections, metadata leaks, and other issues that cause ATS failures.

## Commands

```bash
# Install (editable mode with dev dependencies)
pip install -e ".[dev]"

# Run CLI
ats-check check resume.pdf              # Analyze a single PDF
ats-check check file1.pdf file2.pdf     # Batch analysis
ats-check check resume.pdf --format html --output report.html
ats-check list-checkers                 # List available checker modules

# Run as module (without install)
python -m ats_checker check resume.pdf

# Lint & Format
ruff check src/
ruff format src/

# Type check
mypy src/

# Test
pytest
pytest tests/test_basic.py              # Single test file
pytest -x                               # Stop on first failure
pytest --cov=ats_checker                # With coverage
```

## Architecture

**Plugin-based checker system with registry pattern.** Each check is an independent module that self-registers via decorator.

### Data Flow

```
CLI (cli.py) → Config (config.py) → Engine (engine.py) → Checkers (checkers/*.py) → CheckReport → Reporters (reporters/*.py)
```

### Key Patterns

**Adding a new checker:** Create a file in `src/ats_checker/checkers/`, subclass `BaseChecker`, set class attributes (`name`, `description`, `severity_on_fail`, `requires_text`), and decorate with `@register_checker`. The `__init__.py` auto-discovers new modules via `pkgutil.iter_modules`, so no manual registration is needed.

**Adding a new reporter:** Subclass `BaseReporter`, set `format_name`, decorate with `@register_reporter`, and import it in `src/ats_checker/reporters/__init__.py`.

**Configuration hierarchy:** Defaults → XDG config (`~/.config/ats-checker/config.toml`) → local `ats-checker.toml` → `--config` flag → env vars (`ATS_CHECKER_` prefix, `__` delimiter for nested) → CLI flags. Each checker has its own Pydantic config model in `config.py`.

### Module Responsibilities

- **`engine.py`** — Orchestrates checker execution. Opens PDF, resolves which checkers to run, pre-extracts text if needed, catches per-checker exceptions, assembles `CheckReport`.
- **`models.py`** — Pydantic v2 models: `Severity`, `Issue`, `CheckerResult`, `CheckReport`, `BatchReport`, `CheckerConfig`.
- **`config.py`** — Pydantic Settings with custom `TomlConfigSettingsSource` for layered TOML loading.
- **`pdf_utils.py`** — `PDFDocument` context manager wrapping both pdfplumber and PyMuPDF handles; `extract_text()`, `extract_font_info()` helpers.
- **`cli.py`** — Typer app with `check` and `list-checkers` commands. Exit codes: 0 (pass), 1 (critical issues), 2 (error).
- **`checkers/`** — 9 checker modules auto-discovered at import time (excludes `base.py` and `registry.py`).
- **`reporters/`** — Terminal (Rich), JSON, and HTML reporters. HTML uses Jinja-style templates in `reporters/templates/`.

## Implementation Status

Phases 1–4 complete (foundation, checker engine, reporters, CLI + batch processing). Phase 5 (testing) is pending — only a placeholder test exists. `scoring.py` is empty, reserved for Phase 7.

## Tool Configuration

All tool settings live in `pyproject.toml`:
- **Ruff**: line-length 100, target Python 3.11, rules E/F/I (Pyflakes, errors, isort)
- **mypy**: strict mode, pydantic plugin, `ignore_missing_imports = true`
- **pytest**: `pythonpath = ["src"]`, `testpaths = ["tests"]`