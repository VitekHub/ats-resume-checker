# Phase 6: Documentation & CI/CD

> Write comprehensive documentation, set up CI/CD automation, and establish
> code quality tooling so the project is maintainable long-term.

## Step 6.1 — Project README (`README.md`)

**Goal:** Create the main project README (separate from the plan README).

- [ ] Structure:
  ```
  # ATS Resume Checker

  > Check PDF resumes for ATS compatibility issues.

  ## Installation
  ## Quick Start
  ## What It Checks
  ## Output Formats
  ## Configuration
  ## CLI Reference
  ## Contributing
  ## License
  ```
- [ ] Installation section:
  - `pip install ats-resume-checker`
  - From source: `pip install -e ".[dev]"`
  - Python version requirement (3.11+)
- [ ] Quick Start section:
  - `ats-check check resume.pdf` — basic usage
  - `ats-check check resume.pdf --format json -o report.json` — JSON output
  - `ats-check check resume.pdf --format html -o report.html` — HTML report
  - Screenshot or ASCII art of terminal output
- [ ] What It Checks section:
  - Table of all checkers with one-line descriptions
  - Link to detailed docs for each checker
- [ ] Output Formats section:
  - Terminal (default), JSON, HTML
  - Example of each
- [ ] Configuration section:
  - TOML file format and location
  - Environment variable overrides
  - All configurable thresholds
- [ ] CLI Reference section:
  - `ats-check check` — all flags and options
  - `ats-check list-checkers` — description
  - Exit codes: 0 (pass), 1 (critical issues), 2 (error)
- [ ] Contributing section:
  - Link to CONTRIBUTING.md
  - Development setup
- [ ] License section

**Acceptance:** README is clear, complete, and renders well on GitHub.

---

## Step 6.2 — API Documentation

**Goal:** Document the public API for programmatic use.

- [ ] Create `docs/api.md`:
  - `Config` — all fields with types, defaults, and descriptions
  - `run_check()` — signature, parameters, return type, example usage
  - `CheckReport` — all fields and computed properties
  - `Issue` — all fields with descriptions
  - `Severity` — enum values
  - `BaseChecker` — how to create a custom checker
  - `BaseReporter` — how to create a custom reporter
  - `get_reporter()` — how to get a reporter by name
- [ ] Add docstrings to all public functions (if not already done):
  - Use Google-style docstrings
  - Include `Args:`, `Returns:`, `Raises:`, `Example:` sections
  - Type hints match docstrings
- [ ] Create `docs/custom-checker.md`:
  - Step-by-step guide to writing a new checker
  - Example: a "links checker" that detects hyperlinks in the PDF
  - How to register it with the `@register_checker` decorator
  - How to test it
- [ ] Create `docs/custom-reporter.md`:
  - Step-by-step guide to writing a new reporter
  - Example: a Markdown reporter
  - How to register it

**Acceptance:** A developer can use `ats_checker` as a library by reading `docs/api.md`.

---

## Step 6.3 — User Guide

**Goal:** Write a guide for end users who are not developers.

- [ ] Create `docs/guide.md`:
  - **What is ATS?** — Brief explanation of Applicant Tracking Systems
  - **Why does ATS compatibility matter?** — Statistics on how many companies use ATS
  - **How to use this tool** — Step-by-step for non-developers
  - **Understanding your results** — How to read the report
  - **Common issues and fixes** — Top 10 ATS problems with solutions:
    1. Scanned image instead of text PDF
    2. Photos and graphics
    3. Multi-column layouts
    4. Tables for formatting
    5. Missing standard sections
    6. No email address
    7. Non-standard fonts
    8. Special characters
    9. Oversized file
    10. Metadata leaking personal info
  - **Resume formatting tips** — General advice for ATS-friendly resumes
  - **FAQ** — Common questions

**Acceptance:** A non-developer can understand what ATS is and how to fix their resume based on the guide.

---

## Step 6.4 — Contributing Guide (`CONTRIBUTING.md`)

**Goal:** Make it easy for others to contribute.

- [ ] Create `CONTRIBUTING.md`:
  - Development setup (clone, install, test)
  - Code style (Ruff, line length, type hints)
  - Commit message conventions
  - Pull request process
  - How to add a new checker (link to custom-checker.md)
  - How to add a new reporter (link to custom-reporter.md)
  - Testing requirements (80% coverage minimum)
  - How to report bugs
  - How to suggest features

**Acceptance:** A new contributor can set up the project and make a PR by following the guide.

---

## Step 6.5 — Changelog (`CHANGELOG.md`)

**Goal:** Track changes following Keep a Changelog format.

- [ ] Create `CHANGELOG.md` with initial entry:
  ```markdown
  ## [0.1.0] - 2025-XX-XX

  ### Added
  - Initial release of ATS Resume Checker
  - 9 checker modules: file_size, images, text_extraction, layout,
    sections, contact_info, fonts, metadata, special_chars
  - 3 output formats: terminal (Rich), JSON, HTML
  - CLI with Typer
  - Configuration via TOML files
  - Batch checking support
  - ATS compatibility scoring
  ```
- [ ] Follow [Keep a Changelog](https://keepachangelog.com/) format
- [ ] Follow [Semantic Versioning](https://semver.org/)

**Acceptance:** Changelog exists with initial release entry.

---

## Step 6.6 — GitHub Actions CI Pipeline

**Goal:** Set up automated testing and quality checks.

- [ ] Create `.github/workflows/ci.yml`:
  ```yaml
  name: CI

  on:
    push:
      branches: [main]
    pull_request:
      branches: [main]

  jobs:
    test:
      runs-on: ubuntu-latest
      strategy:
        matrix:
          python-version: ["3.11", "3.12", "3.13"]
      steps:
        - uses: actions/checkout@v4
        - uses: actions/setup-python@v5
          with:
            python-version: ${{ matrix.python-version }}
        - run: pip install -e ".[dev]"
        - run: ruff check src/ tests/
        - run: mypy src/
        - run: pytest --cov=ats_checker --cov-fail-under=80
    lint:
      runs-on: ubuntu-latest
      steps:
        - uses: actions/checkout@v4
        - uses: actions/setup-python@v5
          with:
            python-version: "3.12"
        - run: pip install -e ".[dev]"
        - run: ruff check src/ tests/
        - run: ruff format --check src/ tests/
        - run: mypy src/
  ```
- [ ] Test on Windows and macOS too (use `runs-on` matrix or separate job)
- [ ] Cache pip dependencies for faster runs
- [ ] Add coverage report as artifact

**Acceptance:** Pushing to `main` or opening a PR triggers CI. All checks pass.

---

## Step 6.7 — Pre-commit Hooks

**Goal:** Catch issues before they reach CI.

- [ ] Create `.pre-commit-config.yaml`:
  ```yaml
  repos:
    - repo: https://github.com/astral-sh/ruff-pre-commit
      rev: v0.4.0
      hooks:
        - id: ruff
          args: [--fix]
        - id: ruff-format
    - repo: https://github.com/pre-commit/mirrors-mypy
      rev: v1.10.0
      hooks:
        - id: mypy
          additional_dependencies: [types-all]
  ```
- [ ] Add trailing whitespace, YAML, large file checks
- [ ] Document setup in CONTRIBUTING.md:
  - `pre-commit install`
  - `pre-commit run --all-files`

**Acceptance:** `pre-commit run --all-files` passes. Committing with linting errors is blocked.

---

## Step 6.8 — Release Automation

**Goal:** Automate version bumps and PyPI publishing.

- [ ] Create `.github/workflows/release.yml`:
  - Trigger on version tag push (e.g., `v0.2.0`)
  - Build wheel and sdist
  - Publish to PyPI (using trusted publisher)
  - Create GitHub release with changelog excerpt
- [ ] Configure `pyproject.toml` for PyPI:
  - Proper classifiers
  - License field
  - Project URLs (homepage, bugs, changelog)
  - Optional dependencies groups
- [ ] Document release process in CONTRIBUTING.md:
  1. Update CHANGELOG.md
  2. Bump version in `pyproject.toml`
  3. Commit and tag: `git tag v0.2.0`
  4. Push tag: `git push origin v0.2.0`
  5. CI handles the rest

**Acceptance:** Pushing a version tag triggers a release to PyPI.

---

## Dependencies

- **Phases 1–4** (implementation) should be complete
- **Phase 5** (testing) should be complete or in progress

## Next Phase

→ [Phase 7: Advanced Features](phase-7-advanced-features.md)