# ATS Resume Checker

A CLI tool that analyzes PDF resumes for ATS (Applicant Tracking System) compatibility. It detects common issues that cause ATS failures — embedded images, garbled text extraction, multi-column layouts, unsafe fonts, missing sections, metadata leaks, and more.

## Prerequisites

- **Python 3.11+** with `pip`
- **Build tools** (Linux only) — PyMuPDF may require `gcc` and `mupdf-dev`. On Debian/Ubuntu: `sudo apt install build-essential libmupdf-dev`

## Installation

```bash
pip install .            # runtime only
pip install -e ".[dev]"  # editable, with dev tools
pip uninstall ats-resume-checker  # remove
```

## Usage

```bash
# Analyze one or more PDFs
ats-check check resume.pdf
ats-check check file1.pdf file2.pdf

# Output formats
ats-check check resume.pdf --format json --output report.json
ats-check check resume.pdf --format html --output report.html

# Select or skip specific checkers
ats-check check resume.pdf --checker file_size --checker images
ats-check check resume.pdf --skip-checker metadata

# Other options
ats-check check resume.pdf --no-color      # disable colors
ats-check check resume.pdf --save-text      # save extracted text as sidecar file
ats-check check resume.pdf --show-config    # print effective config and exit

# List available checkers
ats-check list-checkers
```

Run as a module without installing: `python -m ats_checker check resume.pdf`

Exit codes: **0** = all clear, **1** = critical issues found, **2** = error.

## Checkers

| Name | Description |
|---|---|
| `contact_info` | Detects email and phone number in the resume text |
| `file_size` | Checks PDF file size against common portal upload limits |
| `fonts` | Checks for non-standard or symbol fonts that ATS may not render |
| `images` | Detects embedded images that ATS cannot read |
| `layout` | Detects multi-column layouts and tables that scramble ATS text order |
| `metadata` | Checks PDF metadata for personal information leaks |
| `sections` | Checks for standard resume sections that ATS parsers expect |
| `special_chars` | Flags unusual Unicode characters that may not parse in ATS |
| `text_extraction` | Verifies text can be cleanly extracted in reading order |

## Configuration

Configuration is loaded in priority order (highest wins):

1. CLI flags (`--config`, `--format`, `--no-color`, etc.)
2. Environment variables (`ATS_CHECKER_` prefix, `__` delimiter for nested fields)
3. Config file (searched in order): `--config` path → `./ats-checker.toml` → `~/.config/ats-checker/config.toml`
4. Built-in defaults

Example `ats-checker.toml`:

```toml
[file_size]
warning_kb = 500
critical_kb = 1024

[output]
format = "terminal"
verbose = true
```

## Development

```bash
ruff check src/          # lint
ruff format src/         # format
mypy src/                # type check
pytest                   # run tests
pytest --cov=ats_checker # with coverage
```

See [implementation plan](docs/implementation_plan/) for project phases and status.