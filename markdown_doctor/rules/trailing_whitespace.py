"""Rule to detect and fix trailing whitespace."""

from __future__ import annotations

from typing import List

from markdown_doctor.document import MarkdownDocument
from markdown_doctor.models import Fix, Issue, Severity
from markdown_doctor.rules.base import BaseRule


class TrailingWhitespaceRule(BaseRule):
    """Detects trailing spaces and tabs on lines."""

    rule_id = "trailing-whitespace"
    description = "Checks for unwanted trailing spaces or tabs at line ends."
    severity = Severity.WARNING
    fixable = True

    def __init__(self, allow_hard_breaks: bool = False) -> None:
        self.allow_hard_breaks = allow_hard_breaks

    def check(self, doc: MarkdownDocument) -> List[Issue]:
        issues: List[Issue] = []

        for idx, line in enumerate(doc.lines):
            line_num = idx + 1
            # Check trailing whitespace
            stripped = line.rstrip(" \t")
            trailing_len = len(line) - len(stripped)

            if trailing_len == 0:
                continue

            # If user explicitly allows 2 trailing spaces for markdown hard break:
            if (
                self.allow_hard_breaks
                and trailing_len == 2
                and line.endswith("  ")
                and not doc.is_line_in_code_fence(line_num)
            ):
                continue

            fix = Fix(
                description="Remove trailing whitespace",
                replacement=stripped,
                start_line=line_num,
                start_col=1,
                end_line=line_num,
                end_col=len(line) + 1,
            )

            issues.append(
                Issue(
                    rule_id=self.rule_id,
                    message=f"Line has {trailing_len} trailing whitespace character(s).",
                    file_path=doc.file_path,
                    line=line_num,
                    column=len(stripped) + 1,
                    severity=self.severity,
                    fixable=True,
                    fix=fix,
                    context=repr(line[-min(len(line), 20) :]),
                )
            )

        return issues
