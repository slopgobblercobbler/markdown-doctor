"""Rule to detect broken internal anchors and relative file links."""

from __future__ import annotations

import difflib
from pathlib import Path
from typing import Dict, List, Optional
import urllib.parse

from markdown_doctor.document import MarkdownDocument
from markdown_doctor.models import Fix, Issue, Severity
from markdown_doctor.rules.base import BaseRule


class BrokenAnchorRule(BaseRule):
    """Detects broken internal anchor links and missing relative file targets."""

    rule_id = "broken-anchor-link"
    description = "Checks that internal anchors (#heading) and relative file links resolve."
    severity = Severity.ERROR
    fixable = True

    def __init__(self) -> None:
        # Cache for parsed target docs to avoid re-parsing during multi-link checks
        self._target_doc_cache: Dict[str, MarkdownDocument] = {}

    def check(self, doc: MarkdownDocument) -> List[Issue]:
        issues: List[Issue] = []
        valid_slugs = doc.slug_tracker.slugs

        for link in doc.links:
            if link.is_image:
                continue

            url = link.url.strip()
            if not url or url.startswith(("http://", "https://", "mailto:", "ftp://", "javascript:")):
                continue

            # Case 1: Intra-document anchor link: #my-heading
            if url.startswith("#"):
                anchor = url[1:].strip()
                if not anchor:
                    # Pure # is handled by empty link rule
                    continue

                # Unquote URL encoding, e.g. %20 -> space
                unquoted_anchor = urllib.parse.unquote(anchor).lower()

                if not doc.slug_tracker.contains(unquoted_anchor):
                    # Attempt fuzzy match
                    close_matches = difflib.get_close_matches(
                        unquoted_anchor, list(valid_slugs), n=1, cutoff=0.6
                    )

                    msg = f"Broken anchor '#{anchor}' - no matching heading or HTML anchor found."
                    fix: Optional[Fix] = None
                    is_fixable = False

                    if close_matches:
                        suggested = close_matches[0]
                        msg += f" Did you mean '#{suggested}'?"
                        # Provide automated fix
                        new_target = f"#{suggested}"
                        fix = Fix(
                            description=f"Update anchor to '#{suggested}'",
                            replacement=f"[{link.text}]({new_target})",
                            start_line=link.line,
                            start_col=link.column,
                            end_line=link.line,
                            end_col=link.column + len(link.raw),
                        )
                        is_fixable = True

                    issues.append(
                        Issue(
                            rule_id=self.rule_id,
                            message=msg,
                            file_path=doc.file_path,
                            line=link.line,
                            column=link.column,
                            severity=self.severity,
                            fixable=is_fixable,
                            fix=fix,
                            context=link.raw,
                        )
                    )
                continue

            # Case 2: Relative file link: ./path/to/file.md or path/file.md#anchor
            if link.is_relative:
                # Split path and anchor
                file_target = url
                sub_anchor: Optional[str] = None
                if "#" in url:
                    file_target, sub_anchor = url.split("#", 1)

                file_target = urllib.parse.unquote(file_target)

                # Skip if empty file target
                if not file_target:
                    continue

                # Check if file exists relative to doc.file_path
                base_dir = doc.file_path.parent if doc.file_path.parent else Path(".")
                target_path = (base_dir / file_target).resolve()

                if not target_path.exists():
                    issues.append(
                        Issue(
                            rule_id="broken-relative-link",
                            message=f"Broken relative link: referenced file '{file_target}' does not exist.",
                            file_path=doc.file_path,
                            line=link.line,
                            column=link.column,
                            severity=Severity.ERROR,
                            fixable=False,
                            context=link.raw,
                        )
                    )
                elif sub_anchor and target_path.suffix.lower() in (".md", ".markdown"):
                    # Validate sub-anchor in target markdown file
                    target_doc = self._get_or_load_doc(target_path)
                    if target_doc:
                        unquoted_sub = urllib.parse.unquote(sub_anchor).lower()
                        if not target_doc.slug_tracker.contains(unquoted_sub):
                            close_matches = difflib.get_close_matches(
                                unquoted_sub, list(target_doc.slug_tracker.slugs), n=1, cutoff=0.6
                            )
                            msg = (
                                f"Broken cross-file anchor '#{sub_anchor}' in '{file_target}'."
                            )
                            if close_matches:
                                msg += f" Did you mean '#{close_matches[0]}'?"
                            issues.append(
                                Issue(
                                    rule_id="broken-relative-anchor",
                                    message=msg,
                                    file_path=doc.file_path,
                                    line=link.line,
                                    column=link.column,
                                    severity=Severity.ERROR,
                                    fixable=False,
                                    context=link.raw,
                                )
                            )

        return issues

    def _get_or_load_doc(self, path: Path) -> Optional[MarkdownDocument]:
        cache_key = str(path)
        if cache_key in self._target_doc_cache:
            return self._target_doc_cache[cache_key]

        try:
            doc = MarkdownDocument.from_file(path)
            self._target_doc_cache[cache_key] = doc
            return doc
        except Exception:
            return None
