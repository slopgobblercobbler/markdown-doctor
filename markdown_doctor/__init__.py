"""markdown-doctor: Production-grade Markdown linter, anchor validator, and repair doctor."""

from __future__ import annotations

__version__ = "0.1.0"

from markdown_doctor.config import DoctorConfig
from markdown_doctor.doctor import Doctor
from markdown_doctor.document import MarkdownDocument
from markdown_doctor.fixer import MarkdownFixer
from markdown_doctor.models import (
    CheckResult,
    DoctorReport,
    DocCodeFence,
    DocFrontmatter,
    DocHeading,
    DocLink,
    Fix,
    Issue,
    Position,
    Severity,
)
from markdown_doctor.parser import MarkdownParser
from markdown_doctor.reporter import Reporter
from markdown_doctor.slug import HeadingSlugTracker, slugify_heading

__all__ = [
    "__version__",
    "Doctor",
    "DoctorConfig",
    "DoctorReport",
    "CheckResult",
    "Issue",
    "Fix",
    "Position",
    "Severity",
    "DocHeading",
    "DocLink",
    "DocCodeFence",
    "DocFrontmatter",
    "MarkdownDocument",
    "MarkdownParser",
    "MarkdownFixer",
    "Reporter",
    "HeadingSlugTracker",
    "slugify_heading",
]
