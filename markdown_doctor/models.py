"""Data models for markdown-doctor."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional


class Severity(str, Enum):
    """Issue severity levels."""

    ERROR = "error"
    WARNING = "warning"
    INFO = "info"

    def __str__(self) -> str:
        return self.value


@dataclass
class Position:
    """Position within a source document."""

    line: int
    column: int
    end_line: Optional[int] = None
    end_column: Optional[int] = None


@dataclass
class Fix:
    """Represents an automated fix for an issue."""

    description: str
    replacement: str
    start_line: int
    start_col: int
    end_line: int
    end_col: int


@dataclass
class Issue:
    """Diagnostic issue discovered by a linting rule."""

    rule_id: str
    message: str
    file_path: Path
    line: int
    column: int
    severity: Severity = Severity.ERROR
    fixable: bool = False
    fix: Optional[Fix] = None
    context: Optional[str] = None

    def as_dict(self) -> Dict[str, Any]:
        """Convert issue to JSON-serializable dictionary."""
        return {
            "rule_id": self.rule_id,
            "message": self.message,
            "file": str(self.file_path),
            "line": self.line,
            "column": self.column,
            "severity": self.severity.value,
            "fixable": self.fixable,
            "context": self.context,
        }


@dataclass
class DocHeading:
    """Parsed markdown heading."""

    level: int
    text: str
    slug: str
    line: int
    raw: str


@dataclass
class DocLink:
    """Parsed markdown or HTML link / image."""

    text: str
    url: str
    line: int
    column: int
    is_image: bool
    raw: str
    anchor: Optional[str] = None
    is_relative: bool = False


@dataclass
class DocCodeFence:
    """Parsed markdown code fence block."""

    fence_char: str
    fence_length: int
    language: str
    start_line: int
    end_line: Optional[int] = None
    is_closed: bool = True
    content: str = ""


@dataclass
class DocFrontmatter:
    """Parsed YAML frontmatter."""

    raw: str
    start_line: int
    end_line: int
    is_closed: bool
    is_valid: bool
    error: Optional[str] = None
    data: Optional[Dict[str, Any]] = None


@dataclass
class CheckResult:
    """Result of running checks on a single document."""

    file_path: Path
    issues: List[Issue] = field(default_factory=list)
    fixed_count: int = 0

    @property
    def is_clean(self) -> bool:
        return len(self.issues) == 0

    @property
    def error_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == Severity.ERROR)

    @property
    def warning_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == Severity.WARNING)


@dataclass
class DoctorReport:
    """Aggregated report across all checked files."""

    results: List[CheckResult] = field(default_factory=list)

    @property
    def total_files(self) -> int:
        return len(self.results)

    @property
    def clean_files(self) -> int:
        return sum(1 for r in self.results if r.is_clean)

    @property
    def total_issues(self) -> int:
        return sum(len(r.issues) for r in self.results)

    @property
    def total_fixed(self) -> int:
        return sum(r.fixed_count for r in self.results)

    @property
    def total_errors(self) -> int:
        return sum(r.error_count for r in self.results)

    @property
    def total_warnings(self) -> int:
        return sum(r.warning_count for r in self.results)

    @property
    def is_clean(self) -> bool:
        return self.total_issues == 0
