"""Rule to detect and fix unclosed markdown code fences."""

from __future__ import annotations

from typing import List

from markdown_doctor.document import MarkdownDocument
from markdown_doctor.models import Fix, Issue, Severity
from markdown_doctor.rules.base import BaseRule


class UnclosedCodeFenceRule(BaseRule):
    """Detects code fences (``` or ~~~) that were opened but never closed."""

    rule_id = "unclosed-code-fence"
    description = "Checks that all code fences (``` or ~~~) have matching closing delimiters."
    severity = Severity.ERROR
    fixable = True

    def check(self, doc: MarkdownDocument) -> List[Issue]:
        issues: List[Issue] = []

        for fence in doc.code_fences:
            if not fence.is_closed:
                closing_delimiter = fence.fence_char * fence.fence_length
                total_lines = len(doc.lines)
                last_line_len = len(doc.lines[-1]) if total_lines > 0 else 0

                fix = Fix(
                    description=f"Close code fence with '{closing_delimiter}' at end of document",
                    replacement=f"\n{closing_delimiter}\n",
                    start_line=total_lines,
                    start_col=last_line_len + 1,
                    end_line=total_lines,
                    end_col=last_line_len + 1,
                )

                issues.append(
                    Issue(
                        rule_id=self.rule_id,
                        message=(
                            f"Unclosed code fence opened at line {fence.start_line} "
                            f"(expected closing '{closing_delimiter}')."
                        ),
                        file_path=doc.file_path,
                        line=fence.start_line,
                        column=1,
                        severity=self.severity,
                        fixable=True,
                        fix=fix,
                        context=doc.get_line(fence.start_line),
                    )
                )

        return issues
