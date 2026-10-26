"""Automated fix engine for resolving markdown-doctor diagnostics."""

from __future__ import annotations

from typing import List, Tuple

from markdown_doctor.models import Fix, Issue


class MarkdownFixer:
    """Applies fixes to markdown document source text."""

    @staticmethod
    def apply_fixes(content: str, issues: List[Issue]) -> Tuple[str, int]:
        """Apply all applicable fixes in reverse document order to preserve offsets.

        Returns (new_content, applied_count).
        """
        # Filter fixable issues with valid Fix objects
        fixable_issues = [i for i in issues if i.fixable and i.fix is not None]
        if not fixable_issues:
            return content, 0

        # Sort descending by line number, then descending by column
        sorted_issues = sorted(
            fixable_issues,
            key=lambda issue: (
                issue.fix.start_line if issue.fix else 0,
                issue.fix.start_col if issue.fix else 0,
            ),
            reverse=True,
        )

        lines = content.splitlines(keepends=True)
        # Check if content ends with a newline
        has_trailing_newline = content.endswith(("\n", "\r\n"))
        # Clean lines to strings without line breaks for indexing
        # but keep track of line endings
        applied = 0

        # Work on a mutable copy of lines (without line endings)
        clean_lines = content.splitlines()

        for issue in sorted_issues:
            fix = issue.fix
            if not fix:
                continue

            # Case A: Append at EOF (e.g. unclosed code fence or frontmatter)
            if fix.start_line > len(clean_lines) or (
                fix.start_line == len(clean_lines) and fix.start_col > len(clean_lines[-1])
            ):
                if fix.replacement.startswith("\n") and not clean_lines:
                    clean_lines.append(fix.replacement.lstrip("\n"))
                elif fix.replacement.startswith("\n"):
                    # Split replacement lines and append
                    sublines = fix.replacement.strip("\n").split("\n")
                    clean_lines.extend(sublines)
                else:
                    clean_lines.append(fix.replacement)
                applied += 1
                continue

            # Case B: Multi-line / single line edits within existing lines
            line_idx = fix.start_line - 1
            if 0 <= line_idx < len(clean_lines):
                target_line = clean_lines[line_idx]

                # Full line replacement (or line trailing whitespace removal)
                if fix.start_col == 1 and (
                    fix.end_col >= len(target_line) + 1 or fix.start_line == fix.end_line
                ):
                    # Replace the entire line or slice
                    clean_lines[line_idx] = fix.replacement
                    applied += 1
                else:
                    # In-line substring replacement
                    col_start = max(0, fix.start_col - 1)
                    col_end = min(len(target_line), fix.end_col - 1)
                    # Slice and splice
                    new_line = (
                        target_line[:col_start]
                        + fix.replacement
                        + target_line[col_end:]
                    )
                    clean_lines[line_idx] = new_line
                    applied += 1

        # Recombine lines
        delimiter = "\r\n" if "\r\n" in content else "\n"
        result = delimiter.join(clean_lines)
        if has_trailing_newline and not result.endswith(delimiter):
            result += delimiter

        return result, applied
