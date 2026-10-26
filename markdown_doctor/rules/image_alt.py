"""Rule to detect and fix missing image alt text."""

from __future__ import annotations

from pathlib import Path
import re
from typing import List
import urllib.parse

from markdown_doctor.document import MarkdownDocument
from markdown_doctor.models import Fix, Issue, Severity
from markdown_doctor.rules.base import BaseRule


class MissingImageAltRule(BaseRule):
    """Detects images missing alt text and provides automated accessibility fixes."""

    rule_id = "missing-image-alt"
    description = "Checks that all images have meaningful alt text for accessibility (WCAG 1.1.1)."
    severity = Severity.WARNING
    fixable = True

    def __init__(self, default_alt_prefix: str = "") -> None:
        self.default_alt_prefix = default_alt_prefix

    def check(self, doc: MarkdownDocument) -> List[Issue]:
        issues: List[Issue] = []

        for link in doc.links:
            if not link.is_image:
                continue

            alt_text = link.text.strip()
            if not alt_text:
                # Generate a sensible fallback from filename or URL
                fallback_alt = self._generate_alt_from_url(link.url)

                fix: Fix | None = None
                raw_tag = link.raw

                if raw_tag.startswith("!["):
                    # Markdown image: ![...](...)
                    # Replace ![...] with ![fallback_alt]
                    # We match ![...]
                    new_tag = re.sub(r"^!\[\s*\]", f"![{fallback_alt}]", raw_tag)
                    fix = Fix(
                        description=f"Add alt text '{fallback_alt}'",
                        replacement=new_tag,
                        start_line=link.line,
                        start_col=link.column,
                        end_line=link.line,
                        end_col=link.column + len(raw_tag),
                    )
                elif raw_tag.lower().startswith("<img"):
                    # HTML <img> tag
                    if "alt=" not in raw_tag.lower():
                        # Insert alt attribute before closing > or />
                        new_tag = re.sub(
                            r"(\s*/?>)$", f' alt="{fallback_alt}"\\1', raw_tag
                        )
                    else:
                        # Replace empty alt="" with alt="fallback"
                        new_tag = re.sub(
                            r"""alt=["']\s*["']""",
                            f'alt="{fallback_alt}"',
                            raw_tag,
                            flags=re.IGNORECASE,
                        )
                    fix = Fix(
                        description=f"Add alt attribute '{fallback_alt}'",
                        replacement=new_tag,
                        start_line=link.line,
                        start_col=link.column,
                        end_line=link.line,
                        end_col=link.column + len(raw_tag),
                    )

                issues.append(
                    Issue(
                        rule_id=self.rule_id,
                        message="Image is missing alt text (accessibility violation WCAG 1.1.1).",
                        file_path=doc.file_path,
                        line=link.line,
                        column=link.column,
                        severity=self.severity,
                        fixable=True,
                        fix=fix,
                        context=link.raw,
                    )
                )

        return issues

    def _generate_alt_from_url(self, url: str) -> str:
        """Derive readable alt text from filename, url, or default."""
        if not url:
            return "Image"

        # Remove query and fragment
        parsed_path = urllib.parse.urlsplit(url).path
        filename = Path(parsed_path).name

        if not filename or filename.startswith("."):
            return "Image"

        stem = Path(filename).stem
        # Clean underscores and dashes
        cleaned = re.sub(r"[-_]+", " ", stem).strip()
        if not cleaned:
            return "Image"

        # Capitalize nicely
        result = cleaned.capitalize()
        if self.default_alt_prefix:
            return f"{self.default_alt_prefix} {result}".strip()
        return result
