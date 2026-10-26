"""Rule to detect and fix invalid YAML frontmatter."""

from __future__ import annotations

import re
from typing import List

from markdown_doctor.document import MarkdownDocument
from markdown_doctor.models import Fix, Issue, Severity
from markdown_doctor.rules.base import BaseRule


class FrontmatterRule(BaseRule):
    """Detects invalid YAML frontmatter syntax, unclosed delimiters, or bad formatting."""

    rule_id = "invalid-frontmatter"
    description = "Checks that document frontmatter uses valid YAML and closed delimiters."
    severity = Severity.ERROR
    fixable = True

    def check(self, doc: MarkdownDocument) -> List[Issue]:
        issues: List[Issue] = []

        fm = doc.frontmatter
        if not fm:
            # Check if file starts with malformed delimiter like '--' or '----' or trailing space
            if doc.lines:
                first_line = doc.lines[0]
                if re.match(r"^--+\s*$", first_line) and first_line.strip() != "---":
                    fix = Fix(
                        description="Normalize frontmatter delimiter to '---'",
                        replacement="---",
                        start_line=1,
                        start_col=1,
                        end_line=1,
                        end_col=len(first_line) + 1,
                    )
                    issues.append(
                        Issue(
                            rule_id=self.rule_id,
                            message=f"Malformed frontmatter opening delimiter '{first_line.strip()}' (expected '---').",
                            file_path=doc.file_path,
                            line=1,
                            column=1,
                            severity=self.severity,
                            fixable=True,
                            fix=fix,
                            context=first_line,
                        )
                    )
            return issues

        # Check unclosed frontmatter
        if not fm.is_closed:
            total_lines = len(doc.lines)
            last_line_len = len(doc.lines[-1]) if total_lines > 0 else 0
            fix = Fix(
                description="Close frontmatter with '---'",
                replacement="\n---\n",
                start_line=total_lines,
                start_col=last_line_len + 1,
                end_line=total_lines,
                end_col=last_line_len + 1,
            )
            issues.append(
                Issue(
                    rule_id=self.rule_id,
                    message="Frontmatter opened with '---' but never closed with matching '---'.",
                    file_path=doc.file_path,
                    line=fm.start_line,
                    column=1,
                    severity=self.severity,
                    fixable=True,
                    fix=fix,
                    context="---",
                )
            )
            return issues

        # Check YAML validity
        if not fm.is_valid:
            error_hint = fm.error or "Invalid YAML syntax"
            issues.append(
                Issue(
                    rule_id=self.rule_id,
                    message=f"Invalid frontmatter YAML: {error_hint}",
                    file_path=doc.file_path,
                    line=fm.start_line,
                    column=1,
                    severity=self.severity,
                    fixable=False,
                    context=doc.lines[0] if doc.lines else "",
                )
            )

        return issues
