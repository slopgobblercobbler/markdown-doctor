"""Markdown document representation and metadata holder."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set

from markdown_doctor.models import (
    DocCodeFence,
    DocFrontmatter,
    DocHeading,
    DocLink,
)
from markdown_doctor.slug import HeadingSlugTracker


@dataclass
class MarkdownDocument:
    """Represents a loaded and tokenized Markdown document."""

    file_path: Path
    raw_content: str
    lines: List[str] = field(default_factory=list)
    frontmatter: Optional[DocFrontmatter] = None
    code_fences: List[DocCodeFence] = field(default_factory=list)
    headings: List[DocHeading] = field(default_factory=list)
    links: List[DocLink] = field(default_factory=list)
    slug_tracker: HeadingSlugTracker = field(default_factory=HeadingSlugTracker)
    code_fence_line_numbers: Set[int] = field(default_factory=set)

    @classmethod
    def from_text(cls, text: str, file_path: Optional[Path] = None) -> MarkdownDocument:
        """Create document instance from string content."""
        from markdown_doctor.parser import MarkdownParser

        path = file_path or Path("untitled.md")
        parser = MarkdownParser()
        return parser.parse(text, path)

    @classmethod
    def from_file(cls, file_path: Path) -> MarkdownDocument:
        """Read and parse a Markdown document from disk."""
        text = file_path.read_text(encoding="utf-8", errors="replace")
        return cls.from_text(text, file_path)

    def is_line_in_code_fence(self, line_num: int) -> bool:
        """Check if 1-indexed line number is inside a code block."""
        return line_num in self.code_fence_line_numbers

    def get_line(self, line_num: int) -> str:
        """Return 1-indexed line content (without trailing newline)."""
        if 1 <= line_num <= len(self.lines):
            return self.lines[line_num - 1]
        return ""
