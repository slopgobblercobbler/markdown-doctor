"""Rule to detect empty or dummy link targets."""

from __future__ import annotations

from typing import List

from markdown_doctor.document import MarkdownDocument
from markdown_doctor.models import Issue, Severity
from markdown_doctor.rules.base import BaseRule


class EmptyLinkUrlRule(BaseRule):
    """Detects links that have empty URLs or placeholder '#' destinations."""

    rule_id = "empty-link-url"
    description = "Checks that links do not have empty destinations or placeholder '#' targets."
    severity = Severity.WARNING
    fixable = False

    def check(self, doc: MarkdownDocument) -> List[Issue]:
        issues: List[Issue] = []

        for link in doc.links:
            url = link.url.strip()
            if not url or url == "#":
                issues.append(
                    Issue(
                        rule_id=self.rule_id,
                        message=f"Link '[{link.text}]' has empty or placeholder target '{url}'.",
                        file_path=doc.file_path,
                        line=link.line,
                        column=link.column,
                        severity=self.severity,
                        fixable=False,
                        context=link.raw,
                    )
                )

        return issues
