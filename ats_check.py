#!/usr/bin/env python3
"""
ATS Compatibility Checker for PDF Resumes/CVs
==============================================

Scans a PDF for common issues that cause Applicant Tracking Systems
to misparse or reject your resume.

Usage:
    python ats_check.py <path-to-resume.pdf>

Install dependencies first:
    pip install -r requirements.txt
"""

import re
import sys
from pathlib import Path

try:
    import pdfplumber
except ImportError:
    print("Missing dependency: pdfplumber. Run: pip install -r requirements.txt")
    sys.exit(2)

try:
    import fitz  # PyMuPDF
except ImportError:
    print("Missing dependency: PyMuPDF. Run: pip install -r requirements.txt")
    sys.exit(2)


# ── ANSI colors for terminal output ──────────────────────────────────────────

RED = "\033[91m"
YELLOW = "\033[93m"
GREEN = "\033[92m"
CYAN = "\033[96m"
BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"


# ── Data classes for results ─────────────────────────────────────────────────


class Issue:
    CRITICAL = "critical"
    WARNING = "warning"
    OK = "ok"

    def __init__(self, severity: str, title: str, detail: str):
        self.severity = severity
        self.title = title
        self.detail = detail

    def __str__(self):
        icon = {
            self.CRITICAL: f"{RED}🔴",
            self.WARNING: f"{YELLOW}🟡",
            self.OK: f"{GREEN}🟢",
        }[self.severity]
        label = {
            self.CRITICAL: f"{RED}CRITICAL",
            self.WARNING: f"{YELLOW}WARNING",
            self.OK: f"{GREEN}OK",
        }[self.severity]
        return f"  {icon} {label}{RESET}  {BOLD}{self.title}{RESET}\n{DIM}     {self.detail}{RESET}"


# ── Checker functions ─────────────────────────────────────────────────────────


def check_file_size(pdf_path: Path) -> Issue:
    """Flag files over 500 KB (common portal upload limit)."""
    size_kb = pdf_path.stat().st_size / 1024
    if size_kb > 1024:
        return Issue(
            Issue.CRITICAL,
            "File too large",
            f"{size_kb:.0f} KB — many portals reject files over 500–1024 KB",
        )
    elif size_kb > 500:
        return Issue(
            Issue.WARNING,
            "File approaching size limit",
            f"{size_kb:.0f} KB — some portals cap uploads at 500 KB",
        )
    else:
        return Issue(
            Issue.OK, "File size is fine", f"{size_kb:.0f} KB — well under typical portal limits"
        )


def check_images(pdf_path: Path) -> list[Issue]:
    """Detect embedded images — photos, icons, charts that ATS can't read."""
    doc = fitz.open(str(pdf_path))
    issues = []

    total_images = 0
    large_images = 0  # images bigger than ~1 inch square
    small_images = 0  # tiny images (likely icons, bullets)

    for page_num in range(len(doc)):
        page = doc[page_num]
        images = page.get_images(full=True)
        total_images += len(images)

        for img in images:
            xref = img[0]
            try:
                base_image = doc.extract_image(xref)
                width = base_image.get("width", 0)
                height = base_image.get("height", 0)
                # Assume ~72 DPI; images > ~72px in both dimensions are "large"
                if width > 72 and height > 72:
                    large_images += 1
                else:
                    small_images += 1
            except Exception:
                large_images += 1  # can't inspect → assume worst

    doc.close()

    if large_images > 0:
        issues.append(
            Issue(
                Issue.CRITICAL,
                "Large images detected (likely a photo or graphic)",
                f"Found {large_images} large image(s). ATS cannot read images — "
                "text inside them is invisible to parsers. Remove any portrait photo, "
                "chart, or infographic.",
            )
        )
    if small_images > 0:
        issues.append(
            Issue(
                Issue.WARNING,
                "Small images/icons detected",
                f"Found {small_images} small image(s). Icons and decorative graphics "
                "can confuse some ATS. Prefer plain text bullets (•) and section headers.",
            )
        )
    if total_images == 0:
        issues.append(
            Issue(
                Issue.OK,
                "No embedded images",
                "PDF contains no images — ATS parsers will read text cleanly.",
            )
        )

    return issues


def check_text_extraction(pdf_path: Path) -> list[Issue]:
    """Check if text can be cleanly extracted in reading order."""
    issues = []
    all_text = ""

    with pdfplumber.open(str(pdf_path)) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                all_text += text + "\n"

    text_length = len(all_text.strip())

    if text_length < 50:
        issues.append(
            Issue(
                Issue.CRITICAL,
                "Almost no extractable text",
                f"Only {text_length} characters extracted. The PDF may be a scanned "
                "image or use custom encoding. ATS will see a blank page.",
            )
        )
        return issues

    # Check for garbled / scrambled text
    # A simple heuristic: ratio of alphabetic characters should be > 60%
    alpha_count = sum(1 for c in all_text if c.isalpha())
    alpha_ratio = alpha_count / max(text_length, 1)

    if alpha_ratio < 0.4:
        issues.append(
            Issue(
                Issue.CRITICAL,
                "Text appears garbled",
                f"Only {alpha_ratio:.0%} alphabetic characters — extracted text looks "
                "scrambled or encoded. ATS will not parse this correctly.",
            )
        )
    elif alpha_ratio < 0.6:
        issues.append(
            Issue(
                Issue.WARNING,
                "Text may have extraction issues",
                f"Alphabetic ratio {alpha_ratio:.0%} is lower than expected. "
                "Some text may not parse correctly in ATS.",
            )
        )
    else:
        issues.append(
            Issue(
                Issue.OK,
                "Text extracts cleanly",
                f"Extracted {text_length:,} characters with {alpha_ratio:.0%} readable content.",
            )
        )

    # Save extracted text for manual review
    text_file = pdf_path.with_suffix(".extracted.txt")
    text_file.write_text(all_text, encoding="utf-8")
    issues.append(
        Issue(
            Issue.OK,
            "Extracted text saved",
            f"Saved to {text_file.name} — review it to see exactly what ATS will read.",
        )
    )

    return issues


def check_columns_and_tables(pdf_path: Path) -> list[Issue]:
    """Detect multi-column layouts and tables that scramble ATS text order."""
    issues = []

    with pdfplumber.open(str(pdf_path)) as pdf:
        for page_num, page in enumerate(pdf.pages):
            # Check for tables
            tables = page.find_tables()
            if tables:
                issues.append(
                    Issue(
                        Issue.WARNING,
                        "Table layout detected",
                        f"Page {page_num + 1}: found {len(tables)} table(s). "
                        "ATS often reads table cells in wrong order. Prefer "
                        "simple section headers with bullet points.",
                    )
                )

            # Check for multi-column layout
            # Heuristic: if words cluster around two distinct X positions
            words = page.extract_words()
            if len(words) > 20:
                x_positions = [w["x0"] for w in words]
                # Check for bimodal distribution (two columns)
                sorted_x = sorted(set(round(x, 0) for x in x_positions))
                if len(sorted_x) > 2:
                    # Find the biggest gap in X positions
                    gaps = [(sorted_x[i + 1] - sorted_x[i], i) for i in range(len(sorted_x) - 1)]
                    gaps.sort(reverse=True)
                    if gaps and gaps[0][0] > 100:  # large horizontal gap = likely 2 columns
                        issues.append(
                            Issue(
                                Issue.WARNING,
                                "Multi-column layout suspected",
                                f"Page {page_num + 1}: text appears in multiple columns. "
                                "ATS reads left-to-right, top-to-bottom — column text "
                                "may get interleaved and jumbled.",
                            )
                        )

    if not any(i.title.startswith("Table") or i.title.startswith("Multi") for i in issues):
        issues.append(
            Issue(
                Issue.OK,
                "Single-column layout detected",
                "Text appears in a single column — ATS will read it in order.",
            )
        )

    return issues


def check_sections(pdf_path: Path) -> list[Issue]:
    """Check for standard resume sections that ATS expects to find."""
    issues = []

    with pdfplumber.open(str(pdf_path)) as pdf:
        all_text = ""
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                all_text += text + "\n"

    text_lower = all_text.lower()

    # Sections that ATS parsers typically look for
    expected_sections = {
        "experience": [
            "experience",
            "work experience",
            "employment",
            "professional experience",
            "work history",
            "career history",
        ],
        "education": ["education", "academic", "qualifications", "degree"],
        "skills": [
            "skills",
            "technical skills",
            "core competencies",
            "competencies",
            "technologies",
            "proficiencies",
        ],
    }

    # Contact info patterns
    contact_patterns = [
        r"\b[\w.-]+@[\w.-]+\.\w{2,}\b",  # email
        r"\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b",  # US-style phone
        r"\b\d{3}\s\d{3}\s\d{3}\s\d{3}\b",  # Czech-style phone 123 456 789 012
        r"\b\+?\d[\d\s\-().]{7,}\d\b",  # international phone
    ]

    found_sections = {}
    missing_sections = {}

    for section, keywords in expected_sections.items():
        for kw in keywords:
            if kw in text_lower:
                found_sections[section] = kw
                break
        else:
            missing_sections[section] = keywords[0]

    has_email = bool(re.search(contact_patterns[0], all_text))
    has_phone = any(re.search(p, all_text) for p in contact_patterns[1:])

    if missing_sections:
        section_list = ", ".join(missing_sections.keys())
        issues.append(
            Issue(
                Issue.WARNING,
                "Missing common sections",
                f"Could not find: {section_list}. ATS parsers rely on section headers "
                f"to categorize your content. Use standard headers like "
                f"{', '.join(missing_sections.values())}.",
            )
        )
    else:
        issues.append(
            Issue(
                Issue.OK, "All key sections found", "Detected: " + ", ".join(found_sections.keys())
            )
        )

    if not has_email:
        issues.append(
            Issue(
                Issue.CRITICAL,
                "No email address detected",
                "ATS needs your email to contact you. Make sure it's plain text, "
                "not in an image or special font.",
            )
        )
    if not has_phone:
        issues.append(
            Issue(
                Issue.WARNING,
                "No phone number detected",
                "Consider adding a phone number in plain text format.",
            )
        )

    if has_email and has_phone:
        issues.append(
            Issue(Issue.OK, "Contact info found", "Email and phone detected in readable text.")
        )

    return issues


def check_fonts(pdf_path: Path) -> list[Issue]:
    """Check for non-standard or unembedded fonts that ATS may not render."""
    issues = []

    doc = fitz.open(str(pdf_path))
    all_fonts = set()

    for page in doc:
        for block in page.get_text("dict")["blocks"]:
            if block["type"] == 0:  # text block
                for line in block.get("lines", []):
                    for span in line.get("spans", []):
                        font_name = span.get("font", "")
                        all_fonts.add(font_name)

    doc.close()

    # Common ATS-safe fonts
    safe_fonts = {
        "arial",
        "helvetica",
        "timesnewroman",
        "times",
        "calibri",
        "garamond",
        "georgia",
        "verdana",
        "tahoma",
        "trebuchet",
        "courier",
        "couriernew",
        "dejavusans",
        "dejavuserif",
        "notosans",
        "roboto",
        "liberationsans",
        "liberationserif",
    }

    # Symbol/Wingding fonts are red flags
    symbol_fonts = {"symbol", "wingdings", "zapfdingbats", "wingding", "mathfont", "symbolfont"}

    # Normalize font names for comparison
    normalized_fonts = {
        f.lower().replace("-", "").replace(" ", "").replace("_", "") for f in all_fonts
    }
    normalized_safe = {
        f.lower().replace("-", "").replace(" ", "").replace("_", "") for f in safe_fonts
    }
    normalized_symbol = {
        f.lower().replace("-", "").replace(" ", "").replace("_", "") for f in symbol_fonts
    }

    found_symbol = normalized_fonts & normalized_symbol
    found_unsafe = normalized_fonts - normalized_safe - normalized_symbol

    if found_symbol:
        issues.append(
            Issue(
                Issue.CRITICAL,
                "Symbol/decorative fonts detected",
                f"Found: {', '.join(found_symbol)}. Symbol fonts (Wingdings, etc.) "
                "are used for bullet icons or decorations. ATS cannot read them. "
                "Use plain text characters like • or – instead.",
            )
        )
    if found_unsafe:
        # Filter out common embedded font prefixes
        likely_embedded = {
            f
            for f in found_unsafe
            if any(
                f.startswith(p)
                for p in {
                    "cambria",
                    "consola",
                    "cfx",
                    "aabcio",
                    "nimbus",
                    "noto",
                    "source",
                    "freesans",
                }
            )
        }
        unusual = found_unsafe - likely_embedded
        if unusual and len(unusual) <= 5:
            issues.append(
                Issue(
                    Issue.WARNING,
                    "Non-standard fonts detected",
                    f"Fonts: {', '.join(list(unusual)[:5])}. "
                    "Unusual fonts may not render in all ATS. "
                    "Stick to Arial, Calibri, Garamond, or Helvetica.",
                )
            )
        elif len(unusual) > 5:
            issues.append(
                Issue(
                    Issue.WARNING,
                    "Many non-standard fonts",
                    f"{len(unusual)} unusual fonts detected. This can cause "
                    "rendering issues in ATS. Simplify to 1–2 standard fonts.",
                )
            )

    if not found_symbol and (not found_unsafe or found_unsafe <= likely_embedded):
        issues.append(
            Issue(
                Issue.OK,
                "Fonts look ATS-friendly",
                "Detected fonts appear to be standard web-safe varieties.",
            )
        )

    return issues


def check_metadata(pdf_path: Path) -> list[Issue]:
    """Check PDF metadata for personal info leaks or missing info."""
    issues = []

    doc = fitz.open(str(pdf_path))
    metadata = doc.metadata or {}
    doc.close()

    sensitive_fields = {"author", "subject", "creator", "producer"}
    found_sensitive = {k: v for k, v in metadata.items() if k.lower() in sensitive_fields and v}

    personal_leaks = []
    for field, value in found_sensitive.items():
        # Check if the value looks like a real name (not a software name)
        if any(
            kw not in value.lower()
            for kw in [
                "microsoft",
                "adobe",
                "word",
                "latex",
                "libre",
                "ghost",
                "pdf",
                "writer",
                "chrome",
                "safari",
                "macos",
            ]
        ):
            personal_leaks.append(f"{field}: {value}")

    if personal_leaks:
        issues.append(
            Issue(
                Issue.WARNING,
                "Personal info in PDF metadata",
                f"Found: {'; '.join(personal_leaks)}. ATS can read this. "
                "Consider stripping metadata (File → Properties in your PDF editor) "
                "or recreating the PDF with minimal metadata.",
            )
        )
    else:
        issues.append(
            Issue(
                Issue.OK,
                "PDF metadata is clean",
                "No personal information leaked through document properties.",
            )
        )

    return issues


def check_special_characters(pdf_path: Path) -> list[Issue]:
    """Flag unusual Unicode characters that may not parse correctly in ATS."""
    issues = []

    with pdfplumber.open(str(pdf_path)) as pdf:
        all_text = ""
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                all_text += text

    # Characters that are commonly problematic
    problematic_ranges = [
        (0x2000, 0x206F, "General Punctuation (em/en dashes, thin spaces, etc.)"),
        (0x2190, 0x21FF, "Arrows"),
        (0x2500, 0x257F, "Box drawing characters"),
        (0x25A0, 0x25FF, "Geometric shapes (bullets, squares)"),
        (0x2600, 0x26FF, "Miscellaneous symbols"),
        (0x2700, 0x27BF, "Dingbats"),
    ]

    found_chars = {}
    for char in all_text:
        cp = ord(char)
        for start, end, name in problematic_ranges:
            if start <= cp <= end:
                if name not in found_chars:
                    found_chars[name] = []
                if len(found_chars[name]) < 5:  # sample only
                    found_chars[name].append(char)

    if found_chars:
        details = []
        for name, chars in found_chars.items():
            char_display = ", ".join(f"'{c}' (U+{ord(c):04X})" for c in chars)
            details.append(f"{name}: {char_display}")
        issues.append(
            Issue(
                Issue.WARNING,
                "Special characters detected",
                f"Found: {'; '.join(details)}. Some ATS may not render "
                "these correctly. Prefer plain ASCII equivalents "
                "(use - instead of —, * instead of •, etc.).",
            )
        )
    else:
        issues.append(
            Issue(
                Issue.OK, "Characters are ATS-friendly", "No unusual Unicode characters detected."
            )
        )

    return issues


# ── Main report ──────────────────────────────────────────────────────────────


def run_checks(pdf_path: Path) -> list[Issue]:
    """Run all ATS compatibility checks and return all issues."""
    all_issues = []

    all_issues.append(check_file_size(pdf_path))
    all_issues.extend(check_images(pdf_path))
    all_issues.extend(check_text_extraction(pdf_path))
    all_issues.extend(check_columns_and_tables(pdf_path))
    all_issues.extend(check_sections(pdf_path))
    all_issues.extend(check_fonts(pdf_path))
    all_issues.extend(check_metadata(pdf_path))
    all_issues.extend(check_special_characters(pdf_path))

    return all_issues


def print_report(pdf_path: Path, issues: list[Issue]):
    """Print a formatted ATS compatibility report."""
    criticals = [i for i in issues if i.severity == Issue.CRITICAL]
    warnings = [i for i in issues if i.severity == Issue.WARNING]
    oks = [i for i in issues if i.severity == Issue.OK]

    print(f"\n{BOLD}{'═' * 60}{RESET}")
    print(f"{BOLD}  ATS Compatibility Report{RESET}")
    print(f"  {DIM}{pdf_path.name}{RESET}")
    print(f"{BOLD}{'═' * 60}{RESET}\n")

    if criticals:
        print(f"{BOLD}{RED}  CRITICAL ISSUES ({len(criticals)}){RESET}")
        print(f"{RED}  These will likely cause ATS rejection:{RESET}\n")
        for issue in criticals:
            print(issue)
        print()

    if warnings:
        print(f"{BOLD}{YELLOW}  WARNINGS ({len(warnings)}){RESET}")
        print(f"{YELLOW}  These may cause parsing issues:{RESET}\n")
        for issue in warnings:
            print(issue)
        print()

    if oks:
        print(f"{BOLD}{GREEN}  PASSED ({len(oks)}){RESET}\n")
        for issue in oks:
            print(issue)
        print()

    # Summary
    print(f"{BOLD}{'═' * 60}{RESET}")
    if criticals:
        print(
            f"{RED}{BOLD}  ✗ NOT ATS-FRIENDLY{RESET} — "
            f"{len(criticals)} critical issue(s) must be fixed"
        )
    elif warnings:
        print(
            f"{YELLOW}{BOLD}  ⚠ LIKELY ATS-COMPATIBLE{RESET} — {len(warnings)} warning(s) to review"
        )
    else:
        print(f"{GREEN}{BOLD}  ✓ ATS-FRIENDLY{RESET} — no issues detected")
    print(f"{BOLD}{'═' * 60}{RESET}\n")

    return len(criticals)


def main():
    if len(sys.argv) < 2:
        print(f"\n{BOLD}Usage:{RESET} python ats_check.py <resume.pdf>")
        print(f"\n{DIM}Checks a PDF resume/CV for common ATS compatibility issues.{RESET}")
        print(f"{DIM}Install dependencies first: pip install -r requirements.txt{RESET}\n")
        sys.exit(2)

    pdf_path = Path(sys.argv[1])

    if not pdf_path.exists():
        print(f"\n{RED}Error: File not found: {pdf_path}{RESET}\n")
        sys.exit(2)

    if pdf_path.suffix.lower() != ".pdf":
        print(f"\n{RED}Error: Not a PDF file: {pdf_path}{RESET}\n")
        sys.exit(2)

    issues = run_checks(pdf_path)
    critical_count = print_report(pdf_path, issues)

    sys.exit(1 if critical_count > 0 else 0)


if __name__ == "__main__":
    main()
