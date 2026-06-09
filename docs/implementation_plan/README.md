# ATS Resume Checker — Implementation Plan

## Overview

This is the implementation plan for rebuilding `ats_check.py` (a 520-line single-file script) into a proper, modular Python project called **ATS Resume Checker**.

The current script works, but it's a monolith — all logic, models, I/O, and CLI in one file with no tests, no configuration system, and no extensibility. This plan transforms it into a well-structured, testable, extensible package.

## Plan Philosophy

- **Incremental** — Each phase builds on the previous one. You can stop after any phase and have a working tool.
- **Testable** — Every component has a clear interface and can be tested in isolation.
- **Extensible** — Adding a new checker or reporter requires zero changes to core code.
- **Configurable** — All thresholds and patterns can be customized via config files.

## Phase Summary

| # | Phase | File | Focus | Estimated Effort |
|---|-------|------|-------|-----------------|
| 1 | Foundation | [phase-1-foundation.md](phase-1-foundation.md) | Project structure, models, config, packaging | 2–3 days |
| 2 | Checker Engine | [phase-2-checker-engine.md](phase-2-checker-engine.md) | Refactor checkers into modular plugins with registry | 3–4 days |
| 3 | Reporters | [phase-3-reporters.md](phase-3-reporters.md) | Terminal (Rich), JSON, HTML output | 2–3 days |
| 4 | CLI & Config | [phase-4-cli-and-config.md](phase-4-cli-and-config.md) | Typer CLI, config files, batch processing | 2–3 days |
| 5 | Testing | [phase-5-testing.md](phase-5-testing.md) | Unit tests, integration tests, coverage | 3–4 days |
| 6 | Docs & CI/CD | [phase-6-docs-and-ci.md](phase-6-docs-and-ci.md) | README, API docs, GitHub Actions, pre-commit | 2–3 days |
| 7 | Advanced Features | [phase-7-advanced-features.md](phase-7-advanced-features.md) | Scoring, comparison, caching, watch mode | 3–4 days |

**Total estimated effort: 17–24 days**

## Dependency Graph

```
Phase 1 (Foundation)
    ↓
Phase 2 (Checker Engine)
    ↓
Phase 3 (Reporters)
    ↓
Phase 4 (CLI & Config)
    ↓
Phase 5 (Testing) ←── can start incrementally after Phase 2
    ↓
Phase 6 (Docs & CI/CD) ←── can start incrementally after Phase 1
    ↓
Phase 7 (Advanced Features)
```

## Key Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Package layout | `src/ats_checker/` | Standard Python src layout, avoids import confusion |
| CLI framework | Typer | Type-safe, auto-generated help, built on Click |
| Terminal output | Rich | Professional tables, progress bars, colors |
| Data models | Pydantic v2 | Validation, serialization, settings integration |
| Configuration | Pydantic Settings + TOML | Type-safe config with env var overrides |
| PDF libraries | pdfplumber + PyMuPDF | Same as original — best combination for text and structure |
| Testing | pytest + pytest-cov | Standard Python testing stack |
| Linting | Ruff | Replaces flake8, isort, black — fast and comprehensive |
| Type checking | mypy (strict) | Catch type errors before runtime |
| Build system | hatchling | Modern, PEP 517 compliant |

## What's NOT in This Plan

- **Web UI** — This is a CLI tool. A web interface would be a separate project.
- **Database storage** — Results are not persisted beyond optional JSON/HTML output and caching.
- **AI/ML analysis** — The tool uses heuristic rules, not machine learning. An ML layer could be added later.
- **Resume generation** — This tool only analyzes, it doesn't create or modify resumes.
- **Language detection** — Currently English-only. i18n prep (Phase 7.7) prepares for translation but doesn't implement it.

## Project Files

- [`overview.md`](overview.md) — Full project description, goals, tech stack, target structure
- [`phase-1-foundation.md`](phase-1-foundation.md) — Project setup, models, config, PDF utilities
- [`phase-2-checker-engine.md`](phase-2-checker-engine.md) — Checker plugin architecture and all 9 checkers
- [`phase-3-reporters.md`](phase-3-reporters.md) — Terminal, JSON, and HTML reporters
- [`phase-4-cli-and-config.md`](phase-4-cli-and-config.md) — Typer CLI, TOML config, batch mode
- [`phase-5-testing.md`](phase-5-testing.md) — Unit tests, integration tests, coverage, fixtures
- [`phase-6-docs-and-ci.md`](phase-6-docs-and-ci.md) — Documentation, GitHub Actions, pre-commit, release
- [`phase-7-advanced-features.md`](phase-7-advanced-features.md) — Scoring, comparison, caching, watch mode

## Getting Started

1. Read [`overview.md`](overview.md) for the full picture
2. Start with [Phase 1](phase-1-foundation.md) to set up the project structure
3. Work through phases sequentially
4. Write tests as you go (Phase 5 steps can be done in parallel with implementation)