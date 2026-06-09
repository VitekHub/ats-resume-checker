# Phase 7: Advanced Features

> Add scoring, actionable suggestions, before/after comparison, caching, and
> other features that take the tool from "checker" to "advisor."

## Step 7.1 — ATS Compatibility Score (`scoring.py`)

**Goal:** Compute a numerical ATS compatibility score (0–100) from check results.

- [ ] Design the scoring algorithm:
  - Each severity has a point value:
    - CRITICAL issue: **−15 points**
    - WARNING issue: **−5 points**
    - OK issue: **+2 points**
  - Base score starts at 100
  - Score is clamped to [0, 100]
  - Never goes above 100 even with many OKs
  - Never goes below 0 even with many criticals
- [ ] Create `ScoreBreakdown` model:
  ```python
  class ScoreBreakdown:
      checker_name: str
      issues: list[Issue]
      deduction: int         # points deducted
      max_deduction: int     # worst possible for this checker
  ```
- [ ] Create `calculate_score(result: CheckReport) -> ScoreResult`:
  ```python
  class ScoreResult:
      score: int             # 0–100
      grade: str             # A, B, C, D, F
      breakdown: list[ScoreBreakdown]
      summary: str           # one-line human summary
  ```
- [ ] Grade thresholds:
  - A: 90–100 — "ATS-Friendly"
  - B: 75–89 — "Likely compatible with minor issues"
  - C: 60–74 — "May have parsing issues"
  - D: 40–59 — "Likely to cause ATS problems"
  - F: 0–39 — "Will almost certainly fail ATS parsing"
- [ ] Integrate into `CheckReport` — set `score` field after all checks complete
- [ ] Add `--score` CLI flag to enable/disable score display (default: off for now, add to default in a future version)
- [ ] Display score in all reporters:
  - Terminal: score badge and grade in header
  - JSON: `score` and `grade` fields in summary
  - HTML: prominent score display with color-coded grade

**Acceptance:** `calculate_score()` returns consistent, intuitive scores for known PDFs. A perfect resume scores 100. A scanned image scores near 0.

---

## Step 7.2 — Remediation Advisor

**Goal:** Enhance each Issue with actionable remediation advice.

- [ ] Add `remediation` field to `Issue` model (already in Phase 1, but flesh it out):
  - Every CRITICAL and WARNING issue must have a non-None `remediation`
  - OK issues can have `remediation = None` or a tip
- [ ] Create `remediation` strings for every existing checker:
  - File size: "Reduce file size by compressing images or removing unnecessary pages. Many portals reject files over 500 KB."
  - Images: "Remove portrait photos, charts, and infographics. Use plain text for section headers and bullet points."
  - Text extraction: "Re-export as a text-based PDF. Avoid scanning — use 'Save as PDF' from your editor, not 'Print to PDF' from a scan."
  - Layout: "Switch to a single-column layout. Replace tables with section headers and bullet points."
  - Sections: "Add standard section headers: Experience, Education, Skills. Avoid creative headers like 'My Journey' or 'Where I've Been'."
  - Contact info: "Add your email address as plain text. Avoid contact info in headers/footers or images."
  - Fonts: "Use standard fonts: Arial, Calibri, Garamond, Helvetica, or Times New Roman."
  - Metadata: "Strip personal metadata from your PDF (File → Properties in your editor)."
  - Special characters: "Replace Unicode symbols with ASCII equivalents: use - instead of —, * instead of •, etc."
- [ ] Add `remediation_url` field (optional): link to a docs page with more detail
- [ ] In reporters, display remediation prominently (not just as a footnote)

**Acceptance:** Every CRITICAL and WARNING issue has a specific, actionable `remediation` string.

---

## Step 7.3 — Before/After Comparison

**Goal:** Allow users to compare two versions of a resume to see if fixes worked.

- [ ] Add `compare` CLI command:
  ```python
  @app.command()
  def compare(
      before: Path = typer.Argument(..., help="Original PDF"),
      after: Path = typer.Argument(..., help="Revised PDF"),
  ) -> None:
  ```
- [ ] Run `run_check()` on both files
- [ ] Compute comparison:
  - Issues that were fixed (present in before, absent in after)
  - New issues introduced (absent in before, present in after)
  - Persistent issues (present in both)
  - Score change: before score → after score
- [ ] Display comparison in terminal:
  ```
  Comparison: resume_v1.pdf → resume_v2.pdf
  ══════════════════════════════════════════

  ✅ Fixed:
    • File too large (1024 KB → 480 KB)
    • Multi-column layout detected → Single column

  🆕 New Issues:
    • Missing phone number (was present before)

  ⚠️ Still Present:
    • Non-standard fonts: ComicSans

  Score: 45 → 78 (+33)
  Grade: D → B
  ```
- [ ] Support `--format json` and `--format html` for comparison reports

**Acceptance:** `ats-check compare old.pdf new.pdf` shows a clear before/after comparison with score delta.

---

## Step 7.4 — Caching System

**Goal:** Cache PDF extraction results to avoid re-processing unchanged files.

- [ ] Create `cache.py` with `CheckCache` class:
  - Cache directory: `~/.cache/ats-checker/` (XDG-compliant)
  - Cache key: hash of file content (SHA-256)
  - Cache value: `CheckReport` serialized as JSON
  - TTL: configurable, default 7 days
- [ ] Cache behavior:
  - Before checking, verify if file hash matches a cached result
  - If cache hit and not expired → return cached result
  - If cache miss or expired → run check, cache result
  - `--no-cache` flag to force fresh check
  - `--clear-cache` command to empty the cache
- [ ] Use `CheckReport.model_dump_json()` for serialization
  - Round-trip must be perfect: cache → load → compare to fresh check
- [ ] Add cache statistics to verbose output:
  - "Cache hit: resume.pdf (checked 2 hours ago)"
  - "Cache miss: resume.pdf (checking now)"
- [ ] Handle cache corruption gracefully (delete bad entries, re-check)

**Acceptance:** Running `ats-check check resume.pdf` twice in a row uses cache on second run. Changing the file forces a re-check.

---

## Step 7.5 — Progress Display

**Goal:** Show progress during checking, especially for batch processing.

- [ ] Add Rich progress bar to `run_check()`:
  - Shows checker name as it runs
  - Shows overall progress (1/9 checkers complete)
  - Shows elapsed time per checker
- [ ] For batch processing:
  - Outer progress bar: files processed (1/10 files)
  - Inner progress bar: checkers per file
- [ ] Progress display is:
  - Shown by default in terminal mode (TTY detected)
  - Hidden in JSON/HTML mode (piped output)
  - Hidden with `--quiet` flag
  - Hidden in non-TTY environments (piped, redirected)
- [ ] Use `rich.progress.Progress` with spinner and bar

**Acceptance:** Running a check shows a progress indicator. Piping output to a file suppresses it.

---

## Step 7.6 — Verbose and Quiet Modes

**Goal:** Add `--verbose` and `--quiet` CLI flags for output control.

- [ ] `--verbose` / `-v`:
  - Show all checks including passing ones (terminal reporter default: only show CRITICAL and WARNING)
  - Show execution time per checker
  - Show cache hit/miss info
  - Show extracted text preview (first 500 chars)
  - Show full config used (effective settings)
- [ ] `--quiet` / `-q`:
  - Only show CRITICAL issues
  - No progress bars
  - Minimal output: file path, critical count, score
  - Exit code still reflects all issues (not just visible ones)
- [ ] These are mutually exclusive (`-v` and `-q` cannot be combined)
- [ ] Both flags affect all reporters (JSON includes/excludes fields, HTML shows/hides sections)

**Acceptance:** `--verbose` shows more detail. `--quiet` shows less. They cannot be combined.

---

## Step 7.7 — Internationalization Prep (i18n)

**Goal:** Prepare the codebase for future translation without implementing translations yet.

- [ ] Create `src/ats_checker/i18n.py`:
  - Simple string catalog: `_()` function that returns English strings for now
  - `_("file_too_large")` → "File too large"
  - Easy to extend later with actual translation files
- [ ] Wrap all user-facing strings through `_()`:
  - Issue titles
  - Issue details
  - Remediation text
  - CLI help text
  - Reporter output
- [ ] This is a prep step — no actual translations needed yet
- [ ] Add a note in CONTRIBUTING.md: "All user-facing strings must go through `_()`"

**Acceptance:** All user-facing strings use `_()`. No hardcoded English in core logic (only in `i18n.py`).

---

## Step 7.8 — Watch Mode

**Goal:** Add a `--watch` flag that re-checks when the PDF changes.

- [ ] Add `--watch` flag to `check` command:
  - Uses `watchdog` library for file system monitoring
  - Re-runs check when the PDF file is modified
  - Clears terminal before re-displaying report
  - Shows "Watching for changes... (Ctrl+C to stop)"
- [ ] Only works with single file (not batch)
- [ ] Only works with terminal reporter
- [ ] Graceful exit on Ctrl+C
- [ ] Add `watchdog` as an optional dependency: `pip install ats-resume-checker[watch]`

**Acceptance:** `ats-check check resume.pdf --watch` re-checks on file save.

---

## Dependencies

- **Phases 1–4** must be complete (core implementation)
- **Phase 5** (testing) should be complete
- **Phase 6** (docs/CI) can be in progress

## Notes

These features are prioritized by impact. The scoring system (7.1) and remediation advisor (7.2) are high-value and should be done first. Comparison (7.3) is useful for iterative resume improvement. Caching (7.4) and progress (7.5) improve UX. Verbose/quiet (7.6), i18n prep (7.7), and watch mode (7.8) are nice-to-haves.